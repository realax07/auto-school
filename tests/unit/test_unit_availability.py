"""Unit-тесты домена календаря: чистые хелперы availability
(backend/instructor_availability.py) — без HTTP, TestClient и БД.

Покрывают валидацию intervals нового контракта Спринта 10 (ADR-010):
_hhmm_valid (формат ЧЧ:ММ) и _slot_rows (валидация intervals: легаси-тело,
типы recurring/one_off, дедупликация, таблица ошибок design.md).
Юнит-уровень кейсов TC-S10BE-003 (домен slot_type/slot_date) и
TC-S10BE-007 (невалидный date → 422). Интеграционные проверки
PUT/GET /api/instructor/availability и границы прошлого —
tests/api/test_s10_backend.py (TC-S10BE-002/005/006).
"""
from backend.instructor.instructor_availability import (
    AvailabilityPayload,
    Interval,
    _hhmm_valid,
    _slot_rows,
)


def _payload(*intervals):
    return AvailabilityPayload(intervals=[Interval(**i) for i in intervals])


# ---------------------------------------------------------------- _hhmm_valid
def test_unit_hhmm_valid_accepts_hhmm():
    assert _hhmm_valid("00:00")
    assert _hhmm_valid("09:30")
    assert _hhmm_valid("23:59")


def test_unit_hhmm_valid_rejects_bad_formats():
    assert not _hhmm_valid("24:00")      # час > 23
    assert not _hhmm_valid("9:30")       # без ведущего нуля
    assert not _hhmm_valid("10:5")       # минута без ведущего нуля
    assert not _hhmm_valid("10:60")      # минута > 59
    assert not _hhmm_valid("")
    assert not _hhmm_valid(None)
    assert not _hhmm_valid("10-30")


# ---------------------------------------------------------------- _slot_rows
def test_unit_slot_rows_legacy_body_maps_to_recurring():
    """Легаси-тело (без slot_type/date) → legacy=True, ключи recurring."""
    rows, legacy, err = _slot_rows(_payload(
        {"weekday": 3, "start_time": "16:00", "end_time": "18:00"},
    ))
    assert err is None and legacy is True
    assert rows == [(3, "16:00", "18:00", "recurring", "")]


def test_unit_slot_rows_typed_body_mixed():
    """Тело нового формата: recurring без даты + one_off с датой."""
    rows, legacy, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
         "slot_type": "recurring"},
        {"weekday": 4, "start_time": "12:00", "end_time": "13:00",
         "slot_type": "one_off", "date": "2026-11-06"},  # 2026-11-06 — пятница
    ))
    assert err is None and legacy is False
    assert rows == [
        (1, "09:00", "10:00", "recurring", ""),
        (4, "12:00", "13:00", "one_off", "2026-11-06"),
    ]


def test_unit_slot_rows_deduplicates_identical_keys():
    """Дубликаты (с учетом slot_type/date) схлопываются (design.md)."""
    rows, legacy, err = _slot_rows(_payload(
        {"weekday": 2, "start_time": "10:00", "end_time": "11:00"},
        {"weekday": 2, "start_time": "10:00", "end_time": "11:00"},
    ))
    assert err is None and legacy is True
    assert rows == [(2, "10:00", "11:00", "recurring", "")]


def test_unit_slot_rows_weekday_out_of_range():
    _, _, err = _slot_rows(_payload(
        {"weekday": 7, "start_time": "10:00", "end_time": "11:00"},
    ))
    assert err == "День недели: целое число от 0 (пн) до 6 (вс)"


def test_unit_slot_rows_bad_time_format():
    _, _, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "9:00", "end_time": "10:00"},
    ))
    assert err == "Время: укажите границы интервала в формате ЧЧ:ММ"


def test_unit_slot_rows_start_not_before_end():
    _, _, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "18:00", "end_time": "18:00"},
    ))
    assert err == "Интервал: начало должно быть раньше конца"


def test_unit_slot_rows_one_off_bad_date():
    _, _, err = _slot_rows(_payload(
        {"weekday": 5, "start_time": "12:00", "end_time": "13:00",
         "slot_type": "one_off", "date": "2026-02-30"},  # несуществующая
    ))
    assert err == (
        "Дата разового слота: укажите существующую дату в формате ГГГГ-ММ-ДД")


def test_unit_slot_rows_one_off_weekday_mismatch():
    """2026-11-06 — пятница (weekday=4), указан 1 (вт) → ошибка."""
    _, _, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "12:00", "end_time": "13:00",
         "slot_type": "one_off", "date": "2026-11-06"},
    ))
    assert err == (
        "День недели разового слота: не совпадает с днем недели даты")


def test_unit_slot_rows_recurring_with_date_rejected():
    """Дата указывается только для one_off (MAJ-2/дизайн таблицы ошибок)."""
    _, _, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
         "slot_type": "recurring", "date": "2026-11-06"},
    ))
    assert err == "Дата: указывается только для разового слота (one_off)"


def test_unit_slot_rows_unknown_type_rejected():
    _, _, err = _slot_rows(_payload(
        {"weekday": 1, "start_time": "09:00", "end_time": "10:00",
         "slot_type": "weekly"},
    ))
    assert err == "Тип слота: укажите 'recurring' или 'one_off'"
