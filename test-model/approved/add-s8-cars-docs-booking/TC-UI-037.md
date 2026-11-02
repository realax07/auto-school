# TC-UI-037 — «Мои брони» ученика: карточка авто с авторизованным фото рядом со слотами (NFR-23)

- Автотест: `tests/test_ui_playwright.py::test_s8_student_my_bookings_car_card_with_photo`
- Приоритет: Must (NFR-23 — выдача ученику не ломается; карточка авто — изменение change)
- Статус: автоматизирован (rule 6 — TC-ID в docstring теста); кейс партии change add-s8-cars-docs-booking (Спринт 8)
- Трассировка:
  - Requirement: Запросы и брони учеников на слотах календаря (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)
  - Scenario: API-контракты броней и графика не меняются — брони с авто доступны ученику (openspec/changes/add-s8-cars-docs-booking/specs/instructor-availability/spec.md)

## GIVEN / WHEN / THEN
- GIVEN кабинет ученика (/cabinet#/my-bookings) с API, замоканным по РЕАЛЬНЫМ шейпам backend/student_marketplace.py и backend/booking.py: accepted-пара с car {id: 11, car_status: validated, photo_url: /api/instructor/cars/11/photo/front}; слот Пт(3) 14:00–16:00 free; confirmed-бронь с тем же car; PNG-маршрут фото
- WHEN открыт раздел «Мои брони»
- THEN карточка #bk-car-card видна: «Škoda Rapid 2020 · автомат», бейдж статуса авто «Проверено»; фото .bk-car-photo img реально открыто (naturalWidth > 0) и запрошено с X-Session-Token ученика (авторизованная выдача); карточка расположена РЯДОМ СО СЛОТАМИ — нижняя граница карточки не ниже верха сетки слотов #bk-grid; бронь в списке: статус «Подтверждена», содержит «Škoda Rapid»

## Примечание
- Партия change add-s8-cars-docs-booking (Спринт 8); кейсы живут
  трассировкой TC-ID в docstring автотеста (rule 6); полный прогон
  359 passed (integration, лог ПМ).
- Отдельного Scenario под карточку авто в «Моих брони» в specs/*/spec.md
  нет — трассировка ближайшая (NFR-23, контракт Спринта 7/8 photo_url
  брони/пары); гэп зафиксирован для ПМ.
