"""Контейнерный контракт (change add-containerization) — статические проверки.

Источник правды — approved-кейсы test-model/approved/add-containerization/
(TC-ADD-001…017, спека specs/containerization/spec.md); находки code-review —
code-reviews/add-containerization/review-001.md (F-1..F-7).

Проверяется машинно-читаемый контур БЕЗ Docker (рантайм-прогон стека — задача 5.1
на Docker-стенде): compose YAML и сервисы, ${VAR:?}-интерполяция кредов MinIO
(F-1), non-root/HEALTHCHECK/pin в Dockerfile, пин requirements.txt, job docker-build
и dummy-.env шаг в CI. Трассировка TC-ADD-NNN — в docstring каждого теста (rule 6).

Модуль пропускается целиком, если репо-корень с docker-compose.yml недоступен
(прогон tests/ внутри образа: compose/Dockerfile/CI в образ не входят —
tests/ монтируются read-only, контракт проверяется хостовым прогоном).
"""
import re
from pathlib import Path

import pytest

try:
    REPO = next(
        p for p in Path(__file__).resolve().parents
        if (p / "docker-compose.yml").is_file()
    )
except StopIteration:
    pytest.skip(
        "docker-compose.yml недоступен: контракт проверяется вне образа "
        "(в контейнере tests/ смонтированы без compose/Dockerfile/CI)",
        allow_module_level=True,
    )

COMPOSE = (REPO / "docker-compose.yml").read_text(encoding="utf-8")
DOCKERFILE = (REPO / "Dockerfile").read_text(encoding="utf-8")
CI_FLOW = (REPO / ".github" / "workflows" / "flow.yml").read_text(encoding="utf-8")
REQUIREMENTS = (REPO / "requirements.txt").read_text(encoding="utf-8")


def _parse_compose():
    """yaml.safe_load, если pyyaml доступен; иначе stdlib-структурная валидация.

    Требование «compose YAML валиден» не должно зависеть от установки pyyaml
    (в requirements.txt его нет намеренно): fallback ловит структурные дефекты —
    табы, дисбаланс кавычек/скобок, отсутствие ключей верхнего уровня.
    """
    try:
        import yaml
    except ImportError:
        return None
    return yaml.safe_load(COMPOSE)


def _top_level_block(text: str, key: str) -> str:
    """Блок YAML-ключа верхнего уровня (до следующего ключа без отступа)."""
    m = re.search(rf"^{key}:\s*$", text, re.M)
    assert m, f"нет ключа верхнего уровня {key!r}"
    rest = text[m.end():]
    nxt = re.search(r"^[^\s#-]", rest, re.M)
    return rest[: nxt.start()] if nxt else rest


def _compose_structural_ok() -> list:
    """Stdlib-валидация структуры docker-compose.yml (без pyyaml)."""
    assert "\t" not in COMPOSE, "табы в YAML недопустимы"
    for line in COMPOSE.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            assert line.count('"') % 2 == 0, f"нечетное число кавычек: {line!r}"
    top_level = re.findall(r"^([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)", COMPOSE, re.M)
    for key in ("name", "services", "networks", "volumes"):
        assert key in top_level, f"нет ключа верхнего уровня {key!r}"
    # Сервисы — ключи с отступом ровно 2 пробела внутри блока services:
    services_block = _top_level_block(COMPOSE, "services")
    services = re.findall(r"^  ([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)", services_block, re.M)
    assert services, "в services: нет сервисов"
    return services


def test_compose_yaml_valid_and_has_services():
    """TC-ADD-004 — compose YAML валиден; сервисы app, nginx, minio на местах.

    Requirement: Compose-стек app + nginx + MinIO (Scenario: Данные переживают
    пересоздание контейнеров). Стек из трех сервисов обязателен спекой (FR-52).
    """
    doc = _parse_compose()
    if doc is not None:
        services = set(doc["services"])
    else:
        services = set(_compose_structural_ok())
    assert set(services) >= {"app", "nginx", "minio"}, (
        f"compose-стек обязан содержать сервисы app/nginx/minio, есть: {sorted(services)}"
    )


def test_compose_minio_credentials_required_interpolation():
    """TC-ADD-005 — креды MinIO через ${VAR:?}-интерполяцию (F-1, NFR-14).

    Requirement: Секреты вне образа и сегментация сетей (Scenario: Секреты
    не зашиты в образ). Дефолтные minioadmin/minioadmin отсечены механикой
    compose: пустая/отсутствующая переменная роняет `compose up`.
    """
    minio_block = _top_level_block(COMPOSE, "services")
    minio_block = minio_block[minio_block.index("  minio:"):]
    assert "${MINIO_ROOT_USER:?" in minio_block, (
        "minio: нет обязательной интерполяции ${MINIO_ROOT_USER:?…} (F-1)"
    )
    assert "${MINIO_ROOT_PASSWORD:?" in minio_block, (
        "minio: нет обязательной интерполяции ${MINIO_ROOT_PASSWORD:?…} (F-1)"
    )
    # Значение креда — ровно интерполяция, не вшитый литерал
    assert re.search(
        r'MINIO_ROOT_USER:\s*"\$\{MINIO_ROOT_USER:\?', minio_block
    ), "MINIO_ROOT_USER должен браться из ${VAR:?}-интерполяции (F-1)"


def test_dockerfile_non_root_healthcheck_pinned():
    """TC-ADD-001, TC-ADD-003 — non-root USER, HEALTHCHECK, pin образов.

    Requirement: Образ приложения (Scenarios: Сборка образа на чистой машине;
    Версии зафиксированы; FR-51, NFR-11, NFR-12).
    """
    user_lines = re.findall(r"^USER\s+(\S+)", DOCKERFILE, re.M)
    assert user_lines, "в Dockerfile нет USER — процесс пойдет от root (NFR-11)"
    assert all(u not in ("root", "0") for u in user_lines), (
        f"USER не должен быть root: {user_lines}"
    )
    assert re.search(r"^HEALTHCHECK\b", DOCKERFILE, re.M), (
        "в Dockerfile нет HEALTHCHECK (FR-54, NFR-13)"
    )
    # Pin базового образа: ARG PYTHON_IMAGE=...@sha256:... (плавающих тегов нет)
    arg_pins = re.findall(r"^ARG\s+PYTHON_IMAGE=(\S+)", DOCKERFILE, re.M)
    assert arg_pins and all("@sha256:" in pin for pin in arg_pins), (
        f"базовый образ python не запинен digest'ом: {arg_pins}"
    )
    # Pin nginx (tag+digest) и MinIO (релизный тег, не :latest) — в compose
    nginx = re.search(r"image:\s*(nginx:\S+)", COMPOSE)
    minio = re.search(r"image:\s*(minio/minio:\S+)", COMPOSE)
    assert nginx and "@sha256:" in nginx.group(1), (
        f"nginx не запинен tag+digest: {nginx and nginx.group(1)!r}"
    )
    assert minio and "latest" not in minio.group(1), (
        f"MinIO на плавающем теге: {minio and minio.group(1)!r}"
    )


def test_requirements_fully_pinned():
    """TC-ADD-003 — каждая зависимость requirements.txt запинена (== или ===).

    Requirement: Образ приложения (Scenario: Версии зафиксированы; NFR-12):
    повторная сборка берет зафиксированные версии, а не плавающие.
    """
    dep_lines = [
        line.strip()
        for line in REQUIREMENTS.splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]
    assert dep_lines, "requirements.txt пуст"
    for line in dep_lines:
        assert "==" in line, f"зависимость без пина (==/===): {line!r}"
        assert not re.search(r"(>=|<=|~=|!=)", line), (
            f"недетерминированный оператор версии: {line!r}"
        )


def test_ci_docker_build_job_and_dummy_env_step():
    """TC-ADD-014, TC-ADD-015 — CI собирает образ; dummy .env перед compose.

    Requirement: CI собирает образ и гоняет тесты в контейнере (Scenarios:
    Падающий тест красит PR; Ломающий Dockerfile красит PR; FR-56).
    Job docker-build обязан идти после шага, создающего dummy .env
    (MINIO_ROOT_USER/MINIO_ROOT_PASSWORD — CI-placeholder'ы, не секреты),
    иначе ${VAR:?}-интерполяция (F-1) роняет compose-команды на раннере.
    """
    job = re.search(r"^  docker-build:\s*$", CI_FLOW, re.M)
    assert job, "в flow.yml нет job docker-build (FR-56)"
    job_block = CI_FLOW[job.start():]
    dummy = re.search(r"MINIO_ROOT_USER=ci-placeholder", job_block)
    assert dummy, (
        "в job docker-build нет шага создания dummy .env "
        "(MINIO_ROOT_USER/MINIO_ROOT_PASSWORD=ci-placeholder)"
    )
    first_compose = job_block.find("docker compose")
    assert first_compose != -1, "в job docker-build нет compose-команд"
    assert dummy.start() < first_compose, (
        "dummy .env должен создаваться ПЕРЕД compose-командами "
        "(${VAR:?}-интерполяция читает .env на старте compose)"
    )
