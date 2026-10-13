"""GET /api/instructor/dashboard (задача change add-instructor-cabinet,
correlation_id 467fcb39a3234f33b54b95567f4ce656).

Кабинет инструктора: единая точка данных + серверная проверка роли
(FR-18, FR-20; sdd.md «Спринт 2, часть 2», §20.1):

1) проверка сессии (X-Session-Token; 401 {"ok": false} при отсутствии/
   неверном/истекшем/аннулированном токене — механика backend/auth.py,
   паттерн /api/auth/logout и /api/auth/me: контрактное тело {"ok": false},
   не {"detail": ...});
2) SELECT users по user_id сессии (`?`-плейсхолдер, NFR-2) — записи нет →
   401 (вырожденный случай);
3) role != 'instructor' → 403 {"ok": false} (сессия валидна, роль не та —
   distinct от 401 «нет сессии»);
4) ok → 200 {"ok": true, "instructor": {surname, name, patronymic, email},
   "demo": true, ...} — демо-данные макета (stats, schedule, appointments,
   next_lesson, vehicle, operations) константами модуля: содержимое кабинета
   — демонстрационное («Все данные вымышлены», FR-19/FR-21), реальные данные
   БД кабинету не выдаются (design.md, «Сознательные ограничения»).

Ответ и заголовки запроса не логируются (NFR-3).
"""
from fastapi import APIRouter, Header
from fastapi.responses import JSONResponse

import backend.auth as auth
import backend.db as db

router = APIRouter()


def _unauthorized() -> JSONResponse:
    """Тело 401 — {"ok": false} (симметрично auth._unauthorized, §10.3)."""
    return JSONResponse(status_code=401, content={"ok": False})


def _forbidden() -> JSONResponse:
    """Тело 403 — {"ok": false} (сессия валидна, роль не та — FR-18)."""
    return JSONResponse(status_code=403, content={"ok": False})


# Демо-данные кабинета — константы модуля (макет «Все данные вымышлены»,
# FR-19/FR-21; design.md: реальное содержимое разделов — вне объема).
_DEMO_STATS = [
    {"label": "Заработано за месяц", "value": "84 600", "unit": "₽", "foot": "↗ +12% к прошлому месяцу"},
    {"label": "Отработано часов", "value": "62", "unit": "ч", "foot": "из 80 ч план на месяц"},
    {"label": "Мои ученики", "value": "12", "unit": "", "foot": "+3 новых за неделю"},
    {"label": "Занятия сегодня", "value": "4", "unit": "", "foot": "Первое в 10:00"},
]

_DEMO_SCHEDULE = {
    "week": [
        {"day": "ПН", "num": 12, "lessons": 3},
        {"day": "ВТ", "num": 13, "lessons": 2},
        {"day": "СР", "num": 14, "lessons": 3},
        {"day": "ЧТ", "num": 15, "lessons": 2},
        {"day": "ПТ", "num": 16, "lessons": 3},
        {"day": "СБ", "num": 17, "lessons": 1},
        {"day": "ВС", "num": 18, "lessons": 0},
    ],
    "legend": [
        "Занятие подтверждено",
        "Ожидает подтверждения",
        "Свободное окно",
    ],
}

_DEMO_APPOINTMENTS = [
    {"time": "10:00", "duration": "60 минут", "student": "Александр Иванов",
     "type": "Практика · Городской маршрут", "status": "Подтверждено"},
    {"time": "12:00", "duration": "90 минут", "student": "Екатерина Смирнова",
     "type": "Практика · Манёвры и парковка", "status": "Ожидает"},
    {"time": "14:30", "duration": "60 минут", "student": "Дмитрий Волков",
     "type": "Практика · Город", "status": "Подтверждено"},
    {"time": "16:00", "duration": "60 минут", "student": "Свободное окно",
     "type": "Можно открыть запись для ученика", "status": "Свободно"},
]

_DEMO_NEXT_LESSON = {
    "time": "10:00",
    "duration": "60 минут",
    "student": "Александр Иванов",
    "type": "Практика · Город",
    "vehicle": "Škoda Rapid · А123АА",
    "place": "Согласованная локация",
    "goal": "Движение в потоке",
}

_DEMO_VEHICLE = {
    "model": "Škoda Rapid",
    "year": "2020 · Автомат",
    "plate": "А123АА 777",
    "ownership": "Свой автомобиль",
    "documents_progress": 72,
}

_DEMO_OPERATIONS = [
    {"title": "Занятие · Александр Иванов", "when": "Сегодня, 09:00 · Начисление",
     "amount": "+2 000 ₽"},
    {"title": "Занятие · Мария Петрова", "when": "Вчера, 16:00 · Начисление",
     "amount": "+2 000 ₽"},
    {"title": "Расходы на автомобиль", "when": "10 октября · Учёт расходов",
     "amount": "−1 450 ₽"},
]


@router.get("/api/instructor/dashboard")
def instructor_dashboard(
    x_session_token: str | None = Header(default=None, alias="X-Session-Token"),
):
    """Данные кабинета инструктора (§20.1): сессия → SELECT users по id →
    проверка role='instructor' → демо-данные макета + ФИО."""
    # Проверка сессии — публичный helper auth.session_user_id (обертка над
    # _session_user_id, MIN-1): механика require_session, но контрактное
    # тело {"ok": false} вместо {"detail": ...} (паттерн auth.logout/me).
    user_id = auth.session_user_id(x_session_token)
    if user_id is None:
        return _unauthorized()

    conn = db.get_conn()
    try:
        row = conn.execute(
            "SELECT surname, name, patronymic, email, role FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        # Запись users по сессии отсутствует (вырожденный случай) → 401.
        return _unauthorized()
    if row["role"] != "instructor":
        return _forbidden()

    return {
        "ok": True,
        "instructor": {
            "surname": row["surname"],
            "name": row["name"],
            "patronymic": row["patronymic"],
            "email": row["email"],
        },
        "demo": True,
        "stats": _DEMO_STATS,
        "schedule": _DEMO_SCHEDULE,
        "appointments": _DEMO_APPOINTMENTS,
        "next_lesson": _DEMO_NEXT_LESSON,
        "vehicle": _DEMO_VEHICLE,
        "operations": _DEMO_OPERATIONS,
    }
