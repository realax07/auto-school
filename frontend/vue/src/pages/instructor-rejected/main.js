// Спринт 11 (change add-vue-s11-status-forms, задача 1.1): точка входа
// экрана отказа /instructors/rejected. Статическая разметка экрана
// (эквивалент legacy 1:1) — во входном instructors-rejected.html, до
// гидрации видна сразу (мгновенная отрисовка). Поведение страницы —
// App.vue (задача 2.1): причина из sessionStorage
// «instructor_rejected_reason» (пишет модалка входа при route=rejected,
// контракт логина не меняется), ноль запросов к API.
// До задачи 2.1 гидрации нет — модуль держит page-чанк входа в сборке
// (бюджеты NFR-26, check:budgets), поведение добавит App.vue.
document.getElementById('app');
