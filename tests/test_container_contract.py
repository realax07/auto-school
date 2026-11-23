"""Контейнерный контракт (change add-containerization; Спринт 16,
add-wallet-economy 16.0 — стек сокращен до app + nginx) — статические проверки.

Источник правды — approved-кейсы test-model/approved/add-containerization/
(TC-ADD-001…017, спека specs/containerization/spec.md); находки code-review —
code-reviews/add-containerization/review-001.md (F-1..F-7). Спринт 16
(16.0, решение Заказчика 2026-11-14 «Закрой minio»): дельта
specs/containerization REMOVED трехсервисный стек и ADDED «Compose-стек
app + nginx» — сервис minio, volume minio-data, вторая сеть backend,
${MINIO_*:?}-интерполяция и dummy .env-шаг CI удалены; контрактные
тесты переработаны РОВНО по четырем минio-точкам инвентаря design.md.

Проверяется машинно-читаемый контур БЕЗ Docker (рантайм-прогон стека — задача 5.1
на Docker-стенде): compose YAML и сервисы, отсутствие minio в compose
(негатив), non-root/HEALTHCHECK/pin в Dockerfile, пин requirements.txt,
job docker-build и compose-команды CI без dummy-env шага. Трассировка
TC-ADD-NNN — в docstring каждого теста (rule 6).

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


def test_compose_yaml_valid_and_services_exactly_app_nginx_ai_bridge():
    """TC-ADD-004 (ред. 16.0; ред. 19.7) — compose YAML валиден;
    services == {app, nginx, ai-bridge}.

    Requirement (дельта 16.0, ADDED): Compose-стек app + nginx (Scenario:
    В стеке ровно два сервиса и нет S3-хранилища). Трехсервисный стек
    REMOVED решением Заказчика 2026-11-14 «Закрой minio»: сервис minio
    ЗАПРЕЩЕН (вхождение строки — негатив, см. негативный тест ниже).
    Ред. 19.7 (решение Заказчика 2026-11-21 «отдельным сервисом с
    конфигом»): добавлен ai-bridge — GLM-инференс «ГигаЧата» (внутренняя
    сеть, без ports, ключ в gitignored конфиге).
    """
    doc = _parse_compose()
    if doc is not None:
        services = set(doc["services"])
        volumes = set(doc.get("volumes") or {})
    else:
        services = set(_compose_structural_ok())
        volumes = set(re.findall(r"^  ([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)",
                                 _top_level_block(COMPOSE, "volumes"), re.M))
    assert services == {"app", "nginx", "ai-bridge"}, (
        f"compose-стек обязан быть ровно {{app, nginx, ai-bridge}}, "
        f"есть: {sorted(services)}"
    )
    # named volumes — только db/uploads (ai-bridge/content — bind-mounts)
    assert volumes == {"db", "uploads"}, (
        f"volumes обязан быть ровно {{db, uploads}}, есть: {sorted(volumes)}"
    )
    # Сеть backend снята — одна сеть frontend
    networks = set(_top_level_block(COMPOSE, "networks").split())
    network_keys = set(
        re.findall(r"^  ([A-Za-z][A-Za-z0-9_-]*):(?:\s|$)",
                   _top_level_block(COMPOSE, "networks"), re.M)
    )
    assert network_keys == {"frontend"}, (
        f"сети обязаны быть ровно {{frontend}}, есть: {sorted(network_keys)}"
    )


def test_compose_minio_absent():
    """TC-ADD-005 (ред. 16.0) — НЕГАТИВ: S3-хранилище в compose отсутствует.

    Requirement (дельта 16.0, REMOVED «Compose-стек app + nginx + MinIO» /
    ADDED «В стеке ровно два сервиса и нет MinIO»): бывший тест
    ${MINIO_*:?}-интерполяции заменен негативным — ни сервиса minio, ни
    volume minio-data, ни MINIO_*-интерполяций/кредов в compose быть не
    должно (мертвые инструктирующие цепочки недопустимы).
    """
    assert not re.search(r"^\s*minio:\s*$", COMPOSE, re.M), (
        "сервис minio не должен присутствовать в docker-compose.yml (16.0)"
    )
    assert "minio" not in COMPOSE.lower(), (
        "docker-compose.yml должен быть полностью очищен от minio-упоминаний "
        "(сервис/volume/интерполяции/комментарии)"
    )


def test_dockerfile_non_root_healthcheck_pinned():
    """TC-ADD-001, TC-ADD-003 — non-root USER, HEALTHCHECK, pin образов.

    Requirement: Образ приложения (Scenarios: Сборка образа на чистой машине;
    Версии зафиксированы; FR-51, NFR-11, NFR-12). Спринт 16 (16.0): пин
    S3-образа снят из проверок вместе с сервисом; nginx — tag+digest.
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
    # Pin nginx (tag+digest) — в compose; S3-образа в стеке больше нет
    nginx = re.search(r"image:\s*(nginx:\S+)", COMPOSE)
    assert nginx and "@sha256:" in nginx.group(1), (
        f"nginx не запинен tag+digest: {nginx and nginx.group(1)!r}"
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


def test_ci_docker_build_job_compose_without_dummy_env():
    """TC-ADD-014, TC-ADD-015 (ред. 16.0) — CI собирает образ; dummy .env-шага нет.

    Requirement: CI собирает образ и гоняет тесты в контейнере (Scenarios:
    Падающий тест красит PR; Ломающий Dockerfile красит PR; FR-56; дельта
    16.0 Scenario «CI собирает compose без S3-переменных»). Бывший шаг
    создания dummy .env (placeholder-креды под ${VAR:?}-интерполяцию)
    удален из flow.yml — compose-команды выполняются без ручных
    переменных; тест проверяет наличие job docker-build и compose-команд
    и ОТСУТСТВИЕ dummy-env шага перед ними.
    """
    job = re.search(r"^  docker-build:\s*$", CI_FLOW, re.M)
    assert job, "в flow.yml нет job docker-build (FR-56)"
    job_block = CI_FLOW[job.start():]
    first_compose = job_block.find("docker compose")
    assert first_compose != -1, "в job docker-build нет compose-команд"
    assert "ci-placeholder" not in job_block, (
        "dummy .env-шаг (ci-placeholder) должен быть удален из job "
        "docker-build — compose больше не требует обязательных интерполяций"
    )
    assert not re.search(r"Create dummy .env", job_block), (
        "шаг «Create dummy .env» не должен присутствовать в job docker-build"
    )
