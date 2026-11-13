// Спринт 15 (change add-vue-s15-final-migration, задача 1.1): точка входа
// страницы «Страница после регистрации (/registered)». Оболочка — во входном registered.html; полный перенос разметки
// и wiring — задача 3.1 (сейчас — минимальная заглушка App.vue, чтобы вход
// собирался — прецедент arch-review-001 MIN-2 С12, задача 2.1 С14).
// App.vue монтируется поверх #app (паттерн пилота/С11/С12/С14).
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
