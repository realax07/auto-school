// Спринт 12 (change add-vue-s12-landing-apply, задача 2.1 — MIN-2): точка
// входа лендинга /. Статическая разметка страницы (эквивалент legacy 1:1) —
// во входном index.html; Vue монтирует App.vue поверх #app. ПОЛНАЯ
// разметка-копия и wiring js/landing.js 1:1 — задача 3.2 (сейчас —
// минимальная заглушка App.vue, чтобы вход собирался: arch-review-001
// MIN-2; до 3.2 гидрация заменяет статическую разметку заглушкой).
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
