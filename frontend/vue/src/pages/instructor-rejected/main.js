// Спринт 11 (change add-vue-s11-status-forms, задача 2.1): точка входа
// экрана отказа /instructors/rejected. Статическая разметка экрана
// (эквивалент legacy 1:1) — во входном instructors-rejected.html; Vue
// монтирует App.vue поверх #app. Поведение (причина из sessionStorage
// «instructor_rejected_reason») — в App.vue, ноль запросов к API.
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
