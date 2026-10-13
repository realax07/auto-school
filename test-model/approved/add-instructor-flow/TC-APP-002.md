# TC-APP-002 — CTA-кнопки лендинга ведут на анкету /instructors/apply

- ID кейса: TC-APP-002
- ID чеклиста: CHK-2
- Источник: CHK-2 → Requirement «Лендинг инструкторов по прямой ссылке» (домен instructor-application) → FR-10; Scenario «CTA ведут на анкету»
- Тип: позитивный
- Приоритет: Must
- Статус: manual/toBeAutomated (браузерный переход по клику — вне TestClient; косвенный автоконтроль wiring — tests/test_instructor_pages.py::test_instructors_cta_wiring_to_apply: href="/instructors/apply" у всех CTA, location.href='/instructors/apply', отсутствие fetch)

## GIVEN / WHEN / THEN
- GIVEN открыта страница /instructors
- WHEN пользователь поочередно нажимает каждую CTA-кнопку: «Стать инструктором» (шапка/hero), карточки форматов работы («У меня есть свой автомобиль», «Хочу работать на автомобиле Сбера»), нижний CTA («Стать инструктором ↗»)
- THEN каждая из них выполняет переход (навигация, не модалка) на страницу анкеты /instructors/apply

## Предусловия
- Браузер/Playwright с перехватом сети; сервис запущен, /api/health → 200.
- Лендинг /instructors открыт без авторизации.

## Шаги
1. Открыть /instructors.
2. Кликнуть «Стать инструктором» в шапке → зафиксировать итоговый URL.
3. Вернуться назад; кликнуть hero-CTA → зафиксировать URL.
4. Кликнуть каждую карточку формата работы (own и sber) → зафиксировать URL.
5. Кликнуть нижний CTA → зафиксировать URL.
6. Дополнительно (автоконтроль wiring): проверить в HTML наличие href="/instructors/apply" у всех CTA и отсутствие fetch/модальной формы.

## Ожидаемый результат
2–5. Итоговый URL после каждого клика — «/instructors/apply»; анкета открыта.
6. Wiring: все CTA — ссылки/редирект на /instructors/apply; fetch( отсутствует; id="lead-form" и id="modal" отсутствуют.

## Тестовые данные
Тестовые данные не требуются (анонимная навигация).
