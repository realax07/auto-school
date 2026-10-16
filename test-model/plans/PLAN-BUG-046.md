# PLAN-BUG-046: админка — колонка «Действия» наезжает на соседние (скрин Заказчика)

> Флоу: 2 · Автор: dev · Дата: 2026-10-16 · Ветка: fix/bug-046-admin-actions

## Решение Заказчика (дословно)

«Возможно нам вообще не нужны действия в виде столбца. Отклонение и
одобрение только в модалке, которая при нажатию на строку открывается.
На рассмотрении статус сделай желтым».

## Шаги

1. `frontend/admin-dashboard.html`: убрать th/td «Действия» и inline-кнопки
   «Одобрить/Отклонить» из строк; старый внешний deny-box удалить.
2. Модальная карточка (мокап instructor-card-admin, уже согласован):
   для waiting — «Одобрить» (есть) и «Отклонить» → inline-панель с textarea
   «Причина отказа (обязательно)», подтверждение заблокировано до непустого
   комментария (паттерн BUG-045); вызовы существующих approve/deny API.
3. Бейдж «На рассмотрении» (waiting) — желтый
   `.badge.wait{background:#3a2f14;color:#ffc76e;border:1px solid #8a6d1f}`;
   «Одобрена» зеленый / «Отклонена» красный — без изменений.
4. `design/mocks/admin-dashboard.html`: синхронизировать — та же таблица
   без «Действий», желтый wait-бейдж, клик-подсказка (design-guard —
   фрагменты verbatim).
5. `tests/test_ui_playwright.py`: test_admin_moderation_approve_reflects_status
   под новый флоу (клик строки → модалка → Одобрить, колонки «Действия» нет);
   новый тест: pending-строка открывает модалку, «Отклонить» заблокирована
   до комментария, deny → «Отклонена» + причина в списке; желтый бейдж
   waiting (computed style). Фрагментный design-guard page↔mock.

## Прогон

1. pytest tests/test_admin.py tests/test_ui_playwright.py -q
2. pytest tests/ -q --ignore=tests/test_ui_playwright.py
3. python scripts/check_tag_balance.py (баланс тегов HTML)

Коммит в fix/bug-046-admin-actions, не пушить.
