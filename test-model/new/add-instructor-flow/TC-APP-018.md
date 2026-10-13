# TC-APP-018 — Негатив: IntegrityError UNIQUE email — вторая линия защиты, НЕ 500

- ID кейса: TC-APP-018
- ID чеклиста: CHK-18
- Источник: CHK-18 → Requirement «Сохранение заявки со статусом waiting» (домен instructor-application) → FR-16; Scenario «Гонка параллельных сабмитов оставляет ровно одну заявку»; риск review-001-1.1 #1, механика D8 (честное воспроизведение IntegrityError — обертка/monkeypatch, INSERT-конкурент между SELECT и INSERT хендлера)
- Тип: негативный
- Приоритет: Must
- Статус: automated — tests/test_instructors_apply.py::test_apply_race_two_parallel_same_email_only_one_application (ровно одна заявка, вторая → 422) + ::test_apply_integrityerror_second_line_of_defense (дубликат → 422, не 500; INSERT-конкурент эмулирует чужой INSERT между SELECT и INSERT). Уровень честного исполнения IntegrityError-пути (monkeypatch-обертка вокруг conn.execute хендлера) — toBeAutomated (D8: механика на этапе авторства TC). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN email E свободен; две анкеты с email E проходят SELECT-проверки (шаги 8–9 §15.1) до чужого INSERT
- WHEN оба сабмита доходят до INSERT (гонка параллельных сабмитов; симуляция — чужой INSERT между SELECT и INSERT хендлера, детерминированно через monkeypatch-обертку db-слоя)
- THEN в системе РОВНО одна заявка с email E; второй сабмит получает контрактную 422 «Email: уже зарегистрирован» (НЕ 500): sqlite3.IntegrityError от UNIQUE instructor_applications.email перехвачен хендлером

## Предусловия
- Сервис собран через create_app() с роутером instructors; TestClient без сети; чистая БД в tmp, init_db.
- Механика честного покрытия (D8): перехват/обертка момента INSERT (monkeypatch на db.get_conn().execute или вызов между первым SELECT и INSERT), чтобы IntegrityError-ветка исполнялась тестом, а не отсекалась SELECT-проверкой.

## Шаги
1. POST /api/instructors/apply с email instructor@example.com → 200 (первая заявка).
2. Повторный POST с тем же email (прошел SELECT до своего INSERT — путь дубликата) → зафиксировать статус/тело.
3. SELECT COUNT(*) FROM instructor_applications WHERE email = 'instructor@example.com'.
4. Усиление (toBeAutomated, D8): monkeypatch-обертка, пропускающая/откладывающая SELECT-шаги, чтобы INSERT исполнился на занятом email и IntegrityError-ветка хендлера исполнилась реально; зафиксировать ответ.

## Ожидаемый результат
2. 422 {"ok": false, "error": "Email: уже зарегистрирован"} — ни в одном прогоне нет HTTP 500.
3. COUNT = 1.
4. Ответ IntegrityError-пути — та же контрактная 422 (не 500).

## Тестовые данные
Базовый валидный набор (TC-APP-005); email instructor@example.com.
