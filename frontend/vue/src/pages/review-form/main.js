// Спринт 11 (change add-vue-s11-status-forms, задача 1.1): точка входа
// формы отзыва /review (историческое имя артефакта сохранено). Статическая
// разметка экрана (эквивалент legacy 1:1) — во входном review-form.html,
// до гидрации видна сразу. Поведение страницы — App.vue (задача 2.2):
// wiring js/review-form.js 1:1 (сессия, ?instructor=, карточка, звёзды,
// POST /api/student/instructors/{id}/reviews), тосты — shared/utils.js.
// До задачи 2.2 гидрации нет — модуль держит page-чанк входа в сборке
// (бюджеты NFR-26, check:budgets), поведение добавит App.vue.
document.getElementById('app');
