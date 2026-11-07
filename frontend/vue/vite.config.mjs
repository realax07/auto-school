// Спринт 9 (change add-vue-framework-pilot, задача 2.1; ADR-008): каркас
// Vue 3 + Vite — multi-entry MPA (страница = отдельная точка входа, НЕ SPA —
// ОВ-3), vendor-сплит с бюджетами NFR-26.
import { fileURLToPath, URL } from "node:url";

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  // Ассеты ссылаются на /vue/assets/... — префикс вне коллизий с
  // существующей статикой (/js/*, html-входы); отдача — backend/app.py
  // (GET /vue/assets/{path}, задача 2.3).
  base: "/vue/",
  plugins: [vue()],
  build: {
    // Артефакты — frontend/vue/dist (в git НЕ коммитятся — .gitignore).
    outDir: "dist",
    rollupOptions: {
      input: {
        // Пилотная страница (ОВ-4) и страницы Спринта 11 (change
        // add-vue-s11-status-forms, задача 1.1): по одному html-входу на
        // страницу (multi-entry MPA, НЕ SPA — ОВ-3; план ADR-008 С10–С11).
        "instructors-pending": fileURLToPath(
          new URL("./instructors-pending.html", import.meta.url),
        ),
        "instructors-rejected": fileURLToPath(
          new URL("./instructors-rejected.html", import.meta.url),
        ),
        "review-form": fileURLToPath(
          new URL("./review-form.html", import.meta.url),
        ),
      },
      output: {
        // Хэш-имена ассетов — автоматическая cache-инвалидация (design.md).
        entryFileNames: "assets/[name]-[hash].js",
        chunkFileNames: "assets/[name]-[hash].js",
        assetFileNames: "assets/[name]-[hash].[ext]",
        // Vendor-сплит (правила наследуются всеми шагами миграции — ADR-008
        // п.3): runtime Vue → vendor-чанк 'vue'; любой сторонний пакет →
        // отдельный vendor-чанк по пакету (вендорный код не инлайнится в
        // чанки страниц); общий код страниц (api-клиент, утилиты) → чанк
        // 'shared' (свой код, не библиотека).
        manualChunks(id) {
          if (id.includes("node_modules")) {
            const matched = id.match(/node_modules\/((?:@[^/]+\/)?[^/]+)/);
            const pkg = matched ? matched[1] : "vendor";
            if (pkg === "vue" || pkg.startsWith("@vue/")) return "vue";
            return pkg;
          }
          if (id.includes("/src/shared/")) return "shared";
        },
      },
    },
  },
  server: {
    // Dev-режим (design.md): вызовы /api/* — на локальный
    // uvicorn backend.app:app. Прод-эквивалент проверяется только на
    // собранном dist — e2e и приемка идут против сборки.
    proxy: {
      "/api": {
        target: "http://127.0.0.1:8390",
        changeOrigin: true,
      },
    },
  },
});
