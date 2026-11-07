// Спринт 11 (change add-vue-s11-status-forms, задача 2.2): точка входа
// формы отзыва /review (историческое имя артефакта сохранено). Статическая
// разметка экрана (эквивалент legacy 1:1) — во входном review-form.html;
// Vue монтирует App.vue поверх #app. Wiring js/review-form.js 1:1 — в
// App.vue; тосты #toast (вне #app, как legacy) — через shared/utils.js.
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
