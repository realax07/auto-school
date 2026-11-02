<!-- reviewer: code_reviewer (изолированная сессия) | дифф: 1d40a46..HEAD, волна b473703 (backend) | дата: 2026-11-02 -->

# Code review: задача 4.1 (change add-s8-cars-docs-booking)

Проверен дифф `1d40a46..HEAD` (backend-волна b473703): админ-контур
документов в backend/instructor_documents.py — GET /api/admin/documents
(?status, default pending), GET …/{version_id}/file (предпросмотр), POST
…/verify, POST …/reject. Сверено с design.md блок C (X-Admin-Token, 401/422/
404/409, одна транзакция verify, ОВ-1 причина отказа) и tasks.md 4.1.
Покрытие сверено по тестам TC-S8BE-002/003/005 (жизненный цикл verify/reject,
матрица 401/404/422, переключение photo_sts) — полный прогон ПМ 352 passed.

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261102-094136-external

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | backend/instructor_documents.py:489–497 (admin_documents) | ФИО для license берется из users по email анкеты, но при отсутствии user-строки — фолбэк на ФИО из instructor_applications (fio_row = user_row … else app_row). ADR-004/design блок C: «ФИО только из users». В живых данных approved-инструктор всегда есть в users (approve создает запись), фолбэк достижим только на поврежденных данных; задокументирован в docstring | Либо убрать фолбэк (пустая строка в выдаче — админ увидит «—» на фронте), либо оставить с явным комментарием-исключением; на вердикт не влияет |

Не является замечанием (соответствует контракту/решениям):
- 401: без/неверный токен; сессия инструктора/ученика токен не заменяет
  (require_admin → _unauthorized; тест TC-S8BE-005).
- Список: default pending; допустимы pending/verified/rejected; иное → 422;
  license — ФИО, car_sts — марка/модель/госномер + владелец (блок C).
- Предпросмотр: GET …/{version_id}/file → image/* (uploads.image_media_type),
  несуществующий → 404; ОВ-4 (открытие проверяется на фронте — review-007).
- verify: только pending → иначе 409 (двойная защита: SELECT + guard-WHERE
  с rowcount — паттерн NIT-3, гонка check-then-act закрыта); одна
  транзакция: версия verified + decided_at + каноническая колонка
  (license_photo_path/photo_sts) переключается на файл версии; предыдущая
  verified остается архивом.
- reject: тело {reason}; нет/пусто/пробелы → 422 (ОВ-1; CHECK на схеме —
  вторая линия); версия rejected с reject_reason + decided_at; предыдущая
  verified ОСТАЕТСЯ действующей, каноническая колонка не меняется
  (тест TC-S8BE-002).
- SQL статический, параметризованный (NFR-10); причина/ФИО в логах не
  фигурируют (logging в модуле отсутствует).
