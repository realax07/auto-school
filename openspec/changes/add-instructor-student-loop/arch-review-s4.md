# Arch-review s4 — пограничный вердикт (Спринт 4, Партия A, задача 3)

Дата: 2026-10-16. Роль: архитектор. Скоуп: add-s3-frontend-links, ветка feature/s4-links.
Вопрос: поле `instructor_id` в ответе GET /api/student/requests (backend/student_requests.py).

## Что проверено

- `git diff main...HEAD -- backend/student_requests.py`: единственное изменение —
  +4 строки в `my_requests`, добавление `"instructor_id": row["instructor_id"]`
  в элемент ответа (с комментарием о назначении). Прочие поля и логика не тронуты.
- Контекст функции: выборка `WHERE student_id = ?` по сессии ученика
  (require_role "student") — эндпоинт возвращает только СВОИ заявки.
- Дизайн-контракт openspec/changes/add-instructor-student-loop/design.md, Блок 6:
  GET /api/student/requests — «СВОИ заявки: статус, дата, инструктор, deny_comment» (FR-38).

## Вердикт: ДОПУСТИТЬ

Аргументы:

1. Свои заявки ≠ раскрытие чужих данных. Эндпоинт отдаёт данные заявок,
   созданных самим учеником (фильтр по student_id из сессии). Контракт
   «инструкторская колонка раскрытия» (GET /api/instructor/requests) не затронут.
2. Контракт и так раскрывает инструктора ученику: FR-38 включает «инструктор»
   (в реализации — instructor_full_name). instructor_id — тот же уровень
   доступа, ничего нового не открывается.
3. Необходимость: ОВ-2 (повторная заявка после отказа) реализуется
   POST /api/student/requests {instructor_id}; без instructor_id в списке
   «Мои заявки» клиенту физически нечем заполнить повтор — альтернативы
   (второй запрос каталога, хранение на клиенте) были бы сложнее и не надёжнее.
4. Дизайн не противоречит: правило префиксов и ролевая модель соблюдены,
   NFR-3/NFR-4 не задеты (поле в параметризованном SELECT, персональные
   данные сверх контракта не появляются).

## Отражение в дизайне

В design.md, Блок 6, строка GET /api/student/requests дополнена пометкой
«дополнено Спринтом 4, согласовано» с обоснованием (одна строка, как постановлено).

## Валидация

```
$ PATH="$(npm prefix -g)/bin:$PATH" openspec validate --all --strict
- Validating...
✓ change/add-auth-cabinet
✓ change/add-instructor-cabinet
✓ change/add-instructor-flow
✓ change/add-instructor-student-loop
✓ change/add-registration-admin
Totals: 5 passed, 0 failed (5 items)
``` (exit 0)
