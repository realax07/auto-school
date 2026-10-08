"""Конфигурация окружения (NFR-3): секреты только через env, без дефолтов.

Отсутствие обязательной переменной — явная ошибка при старте/использовании,
не тихий дефолт (sdd.md §5).
"""
import os


def _require(name: str) -> str:
    value = os.environ.get(name)
    if not value:
        raise RuntimeError(
            f"Обязательная переменная окружения {name} не задана (см. .env.example)"
        )
    return value


def admin_user() -> str:
    return _require("ADMIN_USER")


def admin_password_hash() -> str:
    return _require("ADMIN_PASSWORD_HASH")
