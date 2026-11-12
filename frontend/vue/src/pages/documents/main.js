// Спринт 14 (change add-vue-s14-instructor-loop, задача 2.1 — MIN-2
// arch-review-001, прецедент С12): точка входа НОВОЙ страницы
// /instructor/documents («Мои документы» — вынос раздела кабинета, Спринт 8;
// legacy-монолит НЕ создается — design-guard BUG-047: страница сразу на
// каркасе). Оболочка страницы — во входном documents.html; Vue монтирует
// App.vue поверх #app. ПОЛНАЯ разметка-копия и wiring (гвард как в
// кабинете, карточная модель раздела С8 1:1) — задача 3.3 (сейчас —
// минимальная заглушка App.vue, чтобы вход собирался).
import { createApp } from 'vue';
import App from './App.vue';

createApp(App).mount('#app');
