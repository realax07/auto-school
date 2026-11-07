<!-- reviewer: ПМ (сборочные задачи верифицированы оркестратором; фактология — прогоны 5.1 и regress-final) | Reviewer-Delegation: deleg-s11-pm-accept-external | дифф: 5d95888…bf9367c + фикс 3c3d47d | дата: 2026-11-07 -->

# Code review: задачи 1.1, 3.2, 4.1, 5.1 (change add-vue-s11-status-forms) — сборка, роуты, бюджеты, финальный прогон

## Вердикт: approve — задачи 1.1, 3.2, 4.1, 5.1 приняты по фактам прогонов ниже.

Периметр: задачи, не покрытые предметным ревью review-001/002 (они
закрывают 2.1/2.2/3.1 и фикс MAJ-1): инфраструктура входов (1.1),
регистрация маршрутов (3.2), бюджеты NFR-26 (4.1), финальный прогон (5.1).

Факты проверок (дерево feat/s11-vue-status-forms, голова 1e222da):

- **1.1** — входы frontend/vue/instructors-rejected.html и
  frontend/vue/review-form.html зарегистрированы в vite.config
  (multi-entry MPA, без vue-router/pinia — соответствие ADR-008);
  shared/utils.js лег в shared-чанк 0.6 КБ (не vendor); новых
  зависимостей в package.json нет.
- **3.2** — _PAGE_ROUTES: точные маршруты /instructors/rejected и /review
  со значениями «vue:…»; механика отдачи сверена с backend/app.py
  (пилотный хендлер /instructors/pending не тронут, 404 без dist
  подтвержден тестом test_new_static_routes_served).
- **4.1** — npm run check:budgets: 3 страницы, vendor vue = 24.1 КБ gzip
  (≤150), первые заходы 25.6/27.1/28.3 КБ gzip (≤200), чужих page-чанков
  нет; воспроизводится на коммите 1e222da.
- **5.1** — полный Playwright-набор: 63 passed, 0 failed (логи прогона
  в спринт-логе; прогон против собранного dist); git diff
  test_ui_playwright.py = ровно 2 переноса источника чтения (утверждения
  дословны, NFR-27).
- Дополнительно: openspec validate add-vue-s11-status-forms --strict и
  --all --strict — 21 passed, 0 failed; regress-final PASS
  (test-model/regress/add-vue-s11-status-forms/regress-final.md,
  failed_tests: []; первый прогон поймал известный таймерный флак
  NFR-001, перепрогон на тихой машине зелен).
