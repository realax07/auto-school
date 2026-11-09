"""Unit-тесты домена PersonalData: парсер артефакта политики (backend/policy.py).

Изолированные тесты ЧИСТОЙ функции read_policy() — без HTTP/TestClient и
без БД: только файл артефакта в tmp_path + env POLICY_FILE (уровень
«unit»; контракт формата — design.md пакета add-personal-data-policy
«Формат артефакта»). Юнит-уровень API-кейсов TC-PD-001 (валидный
артефакт: текст и метаданные), TC-PD-003 и TC-PD-010 (битый/отсутствующий
артефакт — PolicyError, наружу без раскрытия содержимого, NFR-10).
Интеграционные проверки эндпоинтов GET /api/policy и фиксации согласия —
tests/api/test_policy.py.
"""
import pytest

from backend.policy.policy import PolicyError, read_policy

VALID = (
    "policy-version: 1.0\n"
    "policy-date: 2026-11-01\n"
    "---\n"
    "Текст политики персональных данных.\n"
    "Вторая строка текста.\n"
)


@pytest.fixture()
def artifact_file(monkeypatch, tmp_path):
    """Путь к артефакту в tmp_path + env POLICY_FILE на него."""
    path = tmp_path / "policy.md"
    monkeypatch.setenv("POLICY_FILE", str(path))
    return path


def _write(path, content):
    path.write_text(content, encoding="utf-8")


def test_unit_policy_valid_artifact_parsed(artifact_file):
    """Валидный артефакт → {version, date, text}; шапка отделена, текст
    без разделителя и без краевых пустых строк."""
    _write(artifact_file, VALID)
    result = read_policy()
    assert result == {
        "version": "1.0",
        "date": "2026-11-01",
        "text": "Текст политики персональных данных.\nВторая строка текста.",
    }


def test_unit_policy_missing_file_raises(artifact_file):
    """Файла нет → PolicyError без деталей (NFR-10: путь/содержимое не
    раскрываются — у исключения вообще нет аргументов)."""
    with pytest.raises(PolicyError) as exc:
        read_policy()
    assert not exc.value.args


def test_unit_policy_unreadable_bytes_raise(artifact_file):
    """Битый utf-8 (бинарные байты) → PolicyError (UnicodeDecodeError
    внутри парсера конвертируется, наружу — тот же тип без деталей)."""
    artifact_file.write_bytes(b"\xff\xfe\x00broken")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_no_separator_raises(artifact_file):
    """Нет строки '---' → PolicyError (формат design.md нарушен)."""
    _write(artifact_file, "policy-version: 1.0\npolicy-date: 2026-11-01\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_bad_header_line_raises(artifact_file):
    """Строка шапки без ':' (не ключ: значение) → PolicyError."""
    _write(artifact_file, "policy-version 1.0\n---\nТекст\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_missing_version_raises(artifact_file):
    """Нет обязательного policy-version → PolicyError."""
    _write(artifact_file, "policy-date: 2026-11-01\n---\nТекст\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_missing_date_raises(artifact_file):
    """Нет обязательного policy-date → PolicyError (строгость MIN-3
    ревью: наличие даты обязательно, версия непустая обязательна)."""
    _write(artifact_file, "policy-version: 1.0\n---\nТекст\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_bad_date_format_raises(artifact_file):
    """policy-date не ГГГГ-ММ-ДД → PolicyError (формат design.md)."""
    _write(artifact_file, "policy-version: 1.0\npolicy-date: 01.11.2026\n---\nТекст\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_empty_text_raises(artifact_file):
    """Пустой текст после '---' → PolicyError (артефакт поврежден)."""
    _write(artifact_file, "policy-version: 1.0\npolicy-date: 2026-11-01\n---\n\n")
    with pytest.raises(PolicyError):
        read_policy()


def test_unit_policy_header_blank_lines_tolerated(artifact_file):
    """Пустые строки в шапке допускаются (парсер их пропускает)."""
    _write(
        artifact_file,
        "policy-version: 2.0\n\n\npolicy-date: 2026-11-02\n---\nТекст\n",
    )
    result = read_policy()
    assert result["version"] == "2.0"
    assert result["date"] == "2026-11-02"
