# Решение: 2026-10-09-create-change-auth-cabinet

- Дата: 2026-10-09
- Scope: {'project': 'auto-school', 'change_id': 'add-auth-cabinet', 'phase': 1}
- Действие: create_change
- Commit: 43dfea573714e601715f7884461ca7504251cf44
- Источник: чат-лог Telegram 2026-10-08/09

> Цитата: Нужно добавить регистрацию. Данные лежат в базе, мы их еще будем дополнять. Авторизация отдельным сервисом, есть два типа учеток, ученики, водители. Сейчас делаем учеников. Пароли хешируются, в открытом виде не храним. Таблица отдельная.

Журнал решения: «решение зафиксировано», не «личность подтверждена» — журнал в том же репо НЕ является независимым одобрением Заказчика (контракт §10; P0.4).

```decision-record
{
  "action": "create_change",
  "commit": "43dfea573714e601715f7884461ca7504251cf44",
  "date": "2026-10-09",
  "decision_id": "2026-10-09-create-change-auth-cabinet",
  "schema_version": "decision-record/1",
  "scope": {
    "change_id": "add-auth-cabinet",
    "phase": 1,
    "project": "auto-school"
  },
  "source": "чат-лог Telegram 2026-10-08/09"
}
```
