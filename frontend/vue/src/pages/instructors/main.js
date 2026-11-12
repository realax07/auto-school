// Спринт 14 (change add-vue-s14-instructor-loop, задача 2.1 — MIN-2
// arch-review-001, прецедент С12): точка входа лендинга инструкторов
// /instructors. Статическая разметка страницы (эквивалент legacy
// frontend/instructors.html 1:1) — во входном instructors.html; Vue
// монтирует App.vue поверх #app. ПОЛНАЯ разметка-копия и wiring
// js/instructors.js 1:1 + консолидация wiring входа (shared/loginWiring.js,
// LoginModal variant 'instructors') — задача 3.1 (сейчас — минимальная
// заглушка App.vue, чтобы вход собирался; до гидрации видна статическая
// разметка входа).
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
