# TC-MOD-011 — Граница: гонка дубля email при approve → 409 без рассинхрона

- ID кейса: TC-MOD-011
- ID чеклиста: CHK-32
- Источник: CHK-32 → Requirement «Одобрение заявки создает пользователя» (домен admin-moderation) → FR-16; Scenario «Одобрение заявки waiting» (гонка: users.email UNIQUE, sdd §15.3 — IntegrityError как 409)
- Тип: граничный
- Приоритет: Must
- Статус: automated — tests/test_instructor_admin.py::test_approve_transaction_rollback_keeps_consistency (чужой users с тем же email появляется после SELECT заявки → IntegrityError → 409 «Email: уже зарегистрирован», заявка waiting, откат). Плановые ID в docstring действуют до утверждения (rule 6)

## GIVEN / WHEN / THEN
- GIVEN в users уже существует запись с email E заявки (появилась после SELECT-этапов approve — гонка)
- WHEN POST approve этой заявки с валидным админ-токеном
- THEN sqlite3.IntegrityError от UNIQUE users.email обрабатывается как 409 «Email: уже зарегистрирован» (НЕ 500); рассинхрона заявка/пользователь нет: заявка остается waiting, чужая запись users не повреждена

## Предусловия
- Сервис собран через create_app() с роутерами; TestClient без сети; чистая БД в tmp, init_db; waiting-заявка на dup@example.com; чужая users-запись dup@example.com вставлена ПОСЛЕ создания заявки (эмуляция гонки).

## Шаги
1. Создать заявку dup@example.com публичным apply → id A.
2. Прямой INSERT в users (dup@example.com, роль не указана — дефолт student).
3. POST approve {A} с админ-токеном → зафиксировать.
4. Прочитать: users по dup@example.com, заявку A, COUNT(*) FROM users.

## Ожидаемый результат
3. 409 {"ok": false, "error": "Email: уже зарегистрирован"} (IntegrityError перехвачен, не 500).
4. Чужая users-запись цела (нетронута); заявка A — waiting (откат транзакции); COUNT users = 1 — рассинхрона нет.

## Тестовые данные
Заявка — базовый валидный набор (TC-APP-005) с email dup@example.com. Чужая запись: users (surname X, name Y, patronymic Z, dup@example.com, телефон, пароль-хэш-заглушка). Админ: admin / admin-pass-2026.
