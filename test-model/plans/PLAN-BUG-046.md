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

---

# PLAN-BUG-048: не работает загрузка фото (ВУ при регистрации, показ в
# админке, фото автомобилей) — Заказчик 2026-10-21

> Флоу: 2 · Автор: dev · Дата: 2026-10-20 · Ветка: fix/bug-048-photo-uploads

## Диагноз (проверен)

- `frontend/instructor-apply.html`: input #license-file никуда не подключен
  (подпись дословно «макет без реальной загрузки»), сабмит шлет JSON без
  файла. Бэкенд `/api/instructors/apply` УЖЕ умеет multipart с полем
  `license_photo` (backend/instructors.py: sniff_image JPEG/PNG ≤5 МБ по
  magic bytes до записи, сохранение в data/uploads/license/, 422 иначе).
- Админ-выдача ВУ уже есть: GET /api/admin/instructor-applications/{id}
  (license_photo_path) и GET …/{id}/license-image с X-Admin-Token
  (backend/instructor_admin.py); admin-card в admin-dashboard.html УЖЕ
  вызывает оба (fetch blob → objectURL, плейсхолдеры «Файл ВУ не приложен» /
  «Изображение недоступно») — покрытие было только на моках page.route.
- Фото авто: POST/GET /api/instructor/cars/{id}/photo готовы; в my-cars
  (встроен в instructor-dashboard.html) есть загрузка с прогрессом и тосты,
  НЕТ миниатюры до отправки и клиентской предварительной проверки.

## Шаги

1. `frontend/instructor-apply.html` (задача 1):
   - выбор файла → мгновенная миниатюра (img, objectURL) вместо области
     загрузки: `.upload.has-file` скрывает иконку/подпись/кнопку; клик по
     миниатюре заменяет файл (label for=license-file); PDF — карточка
     файла (📄 + имя), т.к. растровой миниатюры нет;
   - клиентская валидация JPEG/PNG/PDF ≤5 МБ: иначе красный текст
     #license-error у поля, отправка блокируется;
   - сабмит → FormData (все поля + license_photo) на
     /api/instructors/apply; ответы 413/415/422 (и любые «Файл: …») —
     видимое сообщение у поля загрузки + notice под формой; 200 →
     /instructors/pending. Тексты «макет без реальной загрузки» /
     «Заявка пока не отправляется» убраны.
2. Админ-карточка (задача 2): код готов ранее — добавляется e2e на ЖИВОМ
   бэкенде (раньше был только мок page.route): заявка с multipart
   license_photo → в карточке изображение; без ВУ → плейсхолдер.
3. my-cars в `frontend/instructor-dashboard.html` (задача 3):
   миниатюра выбранного фото до отправки (#up-thumb, .up-zone.has-thumb,
   клик — заменить), клиентская проверка JPEG/PNG ≤5 МБ (красный текст +
   тост), серверные 413/415/422 — внятный тост с текстом сервера.
4. `tests/test_ui_playwright.py`: TC-UI-020…023 (трассировка
   «TC-UI-0NN (change add-instructor-student-loop): …»):
   - TC-UI-020: загрузка ВУ с миниатюрой, сабмит → pending, файл на
     бэкенде, license-image отдает image/png;
   - TC-UI-021: >5 МБ — клиентский блок с красным текстом; битый .png —
     серверная 422, сообщение у поля, заявка не создана;
   - TC-UI-022: отображение ВУ в админ-карточке (живой бэкенд), плейсхолдер
     у заявки без ВУ;
   - TC-UI-023: my-cars — миниатюра до отправки, ошибка формата → тост,
     валидный PNG → фото в карточке авто.

## Прогон

1. pytest tests/test_ui_playwright.py -q
2. pytest tests/ -q

Коммит в fix/bug-048-photo-uploads, не пушить.

## Примечание (расхождение с буквой тикета)

Бэкенд принимает ВУ только JPEG/PNG (sniff_image); PDF проходит клиентскую
валидацию (JPEG/PNG/PDF ≤5 МБ — по постановке), но сервер ответит 422
«Файл: допустимы только изображения JPEG или PNG» — сообщение показывается
у поля. Если PDF должен приниматься — отдельное решение по бэкенду
(вне скоупа BUG-048, у Заказчика «загрузка фото»).
