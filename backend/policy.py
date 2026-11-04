"""Домен PersonalData (Спринт 9, change add-personal-data-policy, задача 2.1).

Единственный парсер артефакта политики (design.md «Формат артефакта»):
read_policy() читает файл НА КАЖДЫЙ вызов (без кэша — актуальность после
подмены артефакта не зависит от рестарта) по пути POLICY_FILE (env;
дефолт deploy/policy/policy.md — механика AUTOSCHOOL_DB_PATH в db.py).

Формат артефакта (UTF-8 plain text):
    policy-version: 1.0
    policy-date: 2026-11-10
    ---
    <текст: абзацы, разделенные пустой строкой>

Шапка — строки `ключ: значение` ДО первой строки `---`; обязательные
ключи policy-version (непустая строка) и policy-date (YYYY-MM-DD);
неизвестные ключи игнорируются. После `---` — непустой текст. Нарушение
любого правила (нет шапки/ключей/разделителя, пустой текст, файл
отсутствует/нечитаем) → PolicyError: артефакт считается ПОВРЕЖДЕННЫМ.

GET /api/policy — публичный (без префикса роли, механика /api/health):
поврежденный артефакт → 500 {ok:false, error:"Политика: временно
недоступна"}; содержимое артефакта в ответе/логах НЕ раскрывается
(NFR-10 — ошибки логируются без содержимого; здесь — без логов вовсе).

current_policy_version() — хелпер для фиксации согласия (задачи 3.1/4.1
используют при INSERT): версия из артефакта НА МОМЕНТ сабмита; артефакт
поврежден → PolicyError (запись не создается — FR-79).
"""
import os
import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()

# Механика пути — как в db.py (_DEFAULT_DB_PATH): относительный путь от
# корня репозитория/WORKDIR, переопределение переменной окружения.
_DEFAULT_POLICY_FILE = os.path.join("deploy", "policy", "policy.md")

# Контрактная ошибка для /api/policy (design.md): без деталей артефакта.
_UNAVAILABLE_MESSAGE = "Политика: временно недоступна"

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
_REQUIRED_HEADER_KEYS = ("policy-version", "policy-date")


class PolicyError(Exception):
    """Артефакт отсутствует или поврежден (формат design.md нарушен).

    Детали причины (путь, содержимое, системное сообщение) сознательно
    не хранятся и не логируются — NFR-10 (без раскрытия содержимого).
    """


def read_policy() -> dict:
    """Чтение и разбор артефакта на КАЖДЫЙ вызов (без кэша в процессе).

    Возвращает {"version": str, "date": str, "text": str}; нарушение
    формата/чтения → PolicyError (контракт design.md «Формат артефакта»).
    """
    path = os.environ.get("POLICY_FILE", _DEFAULT_POLICY_FILE)
    try:
        with open(path, "r", encoding="utf-8") as fh:
            raw = fh.read()
    except (OSError, UnicodeDecodeError):
        raise PolicyError()

    lines = raw.splitlines()

    # Разделитель `---` обязан быть; до него — шапка, после — текст.
    if "---" not in [line.strip() for line in lines]:
        raise PolicyError()
    separator = next(
        i for i, line in enumerate(lines) if line.strip() == "---"
    )

    header: dict[str, str] = {}
    for line in lines[:separator]:
        if not line.strip():
            continue  # пустые строки шапки допускаем
        key, _, value = line.partition(":")
        if not _:
            raise PolicyError()  # строка не `ключ: значение` — шапка битая
        header[key.strip()] = value.strip()

    for key in _REQUIRED_HEADER_KEYS:
        if not header.get(key):
            raise PolicyError()  # нет обязательного ключа
    if not _DATE_RE.match(header["policy-date"]):
        raise PolicyError()  # policy-date — YYYY-MM-DD (формат design.md)

    text = "\n".join(lines[separator + 1:]).strip()
    if not text:
        raise PolicyError()  # пустой текст — артефакт поврежден

    return {
        "version": header["policy-version"],
        "date": header["policy-date"],
        "text": text,
    }


def current_policy_version() -> str:
    """Версия политики НА МОМЕНТ ВЫЗОВА (хелпер фиксации согласия,
    задачи 3.1/4.1; клиентской версии не доверять — FR-79). Артефакт
    отсутствует/поврежден → PolicyError: вызывающий код обязан ответить
    500 и НЕ создать запись (design.md «Обработка ошибок»)."""
    return read_policy()["version"]


@router.get("/api/policy")
def get_policy():
    """Публичная раздача политики (гость, без авторизации — механика
    /api/health; чтение артефакта на каждый запрос)."""
    try:
        policy = read_policy()
    except PolicyError:
        # Честная ошибка без деталей: содержимое/путь артефакта не
        # раскрываются ни в ответе, ни в логах (NFR-10, NFR-25).
        return JSONResponse(
            status_code=500,
            content={"ok": False, "error": _UNAVAILABLE_MESSAGE},
        )
    return {
        "ok": True,
        "version": policy["version"],
        "date": policy["date"],
        "text": policy["text"],
    }
