# Решение: 2026-11-04-s10-calendar-sa-go

- Дата: 2026-11-04
- Scope: {'project': 'auto-school', 'change_id': 'add-calendar-weeks-availability', 'sprint': 10, 'phase': 1}
- Действие: create_change
- Источник: requirements-sprint10.md (УТВЕРЖДЕН Заказчиком 2026-11-04:
  FR-87…FR-97, NFR-29…NFR-32) + телеграм Заказчика 2026-11-04
  (telegram:144324141, дословно — decisions/2026-11-04-sprint10-calendar-go.md)

> Цитата: В календаре инструктора должна быть возможность смотреть прошлые и будущие недели. Расписание можно выставлять повторяющееся или разовое, это касается каждой ячейки.
>
> Сценарий - при нажатии всплывает графическое мини окошко над ячейкой поверх страницы с выбором, разово или повторяющееся. Можно менять только >= текущей даты/времени.
>
> Календарь должен учитывать реальный календарь на год/месяц (имею в виду число дней, попадание в дни недели и так далее)
>
> у ученика тоже самое, можно смотреть прошлые и будущие недели

Журнал решения: «решение зафиксировано», не «личность подтверждена» — журнал в том же репо НЕ является независимым одобрением Заказчика (контракт §10; P0.4). Вход в Флоу 1 подтвержден: требования Спринта 10 УТВЕРЖДЕНЫ (decisions/2026-11-04-sprint10-calendar-go.md, sprint_scope), план пакета — PLAN.md Спринт 10 (задача 10.2). СА запускает create_change пакета add-calendar-weeks-availability (openspec/changes/add-calendar-weeks-availability/) + ADR-010 (architecture/adr/010-calendar-recurring-availability.md); решения модели (recurring/one_off, миграция, экземпляры) — зона СА в границах FR-90…FR-92, FR-97, NFR-29, NFR-30.

```decision-record
{
  "action": "create_change",
  "date": "2026-11-04",
  "decision_id": "2026-11-04-s10-calendar-sa-go",
  "schema_version": "decision-record/1",
  "scope": {
    "change_id": "add-calendar-weeks-availability",
    "phase": 1,
    "project": "auto-school",
    "sprint": 10
  },
  "source": "requirements-sprint10.md (УТВЕРЖДЕН 2026-11-04) + telegram:144324141 2026-11-04"
}
```
