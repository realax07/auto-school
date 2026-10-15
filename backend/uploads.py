"""uploads.py — helper загрузки изображений (задача 1.1, домен
instructor-documents; переиспользуется фото-эндпоинтами автомобилей).

Безопасность файлов (design.md «Безопасность файлов», NFR-1, NFR-6, ОВ-5):
- валидация ДО записи на диск: magic bytes (JPEG FF D8 FF / PNG
  89 50 4E 47 0D 0A 1A 0A), Content-Type клиента НЕ доверенный;
- лимит 5 МБ (по содержимому);
- имя файла генерирует сервер (<uuid>.<ext>), оригинальные имена
  в путях не участвуют;
- каталог data/uploads/{license,cars}/ вне frontend/ — статикой не
  раздается, прямой URL невозможен (data/ в .gitignore).

Каталог переопределяется env AUTOSCHOOL_UPLOADS_DIR (тесты пишут во
tmp_path, механика AUTOSCHOOL_DB_PATH из conftest).
"""
import os
import uuid
from pathlib import Path

_MAX_IMAGE_BYTES = 5 * 1024 * 1024  # 5 МБ (ОВ-5)
_JPEG_MAGIC = b"\xff\xd8\xff"
_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"

_DEFAULT_UPLOADS_DIR = os.path.join("data", "uploads")


def uploads_dir() -> Path:
    """Корень каталога загрузок (env AUTOSCHOOL_UPLOADS_DIR | data/uploads)."""
    return Path(os.environ.get("AUTOSCHOOL_UPLOADS_DIR", _DEFAULT_UPLOADS_DIR))


def sniff_image(data: bytes) -> tuple[str | None, str | None]:
    """Тип и размер по содержимому (до записи на диск, NFR-6).

    Возвращает (ext, error): ext — 'jpg'/'png' при валидном изображении,
    error — контрактное сообщение 422 («Файл: …») при невалидном.
    Проверка размера перва: файл >5 МБ отклоняется без разбора магии.
    """
    if len(data) > _MAX_IMAGE_BYTES:
        return None, "Файл: изображение больше 5 МБ"
    if data.startswith(_JPEG_MAGIC):
        return "jpg", None
    if data.startswith(_PNG_MAGIC):
        return "png", None
    return None, "Файл: допустимы только изображения JPEG или PNG"


def save_image(kind: str, data: bytes, ext: str) -> str:
    """Сохранение валидного изображения: <uploads>/<kind>/<uuid>.<ext>;
    возвращает сохраненный путь (хранится в БД). kind — 'license' | 'cars'.
    """
    directory = uploads_dir() / kind
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{uuid.uuid4().hex}.{ext}"
    path.write_bytes(data)
    return str(path)


def image_media_type(path: str) -> str:
    """Content-Type выдачи по сохраненному пути (jpg|png; jpeg — дефолт)."""
    return "image/png" if path.lower().endswith(".png") else "image/jpeg"
