// Спринт 14 (change add-vue-s14-instructor-loop, задача 2.1 — MIN-2
// arch-review-001, прецедент С12): точка входа кабинета инструктора
// /instructor/dashboard. Статическая разметка страницы (эквивалент legacy
// frontend/instructor-dashboard.html 1:1) — во входном
// instructor-dashboard.html; Vue монтирует App.vue поверх #app. ПОЛНАЯ
// разметка-копия и wiring dashboard-instructor.js 1:1 (гвард, разделы,
// календарь С10, автомобили С5/С7, документы С8, демо-данные 2.2) —
// задача 3.2 (сейчас — минимальная заглушка App.vue, чтобы вход
// собирался; до гидрации видна статическая разметка входа).
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
