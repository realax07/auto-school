// Спринт 9 (change add-vue-framework-pilot, задача 2.1): точка входа
// пилотной страницы /instructors/pending. Статическая разметка экрана
// (эквивалент legacy) — во входном instructors-pending.html; Vue монтирует
// App.vue поверх #app. Блок 2 (опрос статуса, createApp + таймер опроса и
// его отмена) — задача 3.1, контракт change add-application-status-polling.
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
