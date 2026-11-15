"""Гарды денег Спринта 16 (change add-wallet-economy, задача 16.6.1).

Source-inspection-гварды (прецедент test_qa_sprint1 NFR-002/TC-NFR-002):
инварианты читаются по исходникам HEAD — сборка/сеть не нужны.

  (а) NFR-33 — деньги только целыми копейками, арифметика целочисленная:
      в backend/wallet/**, backend/student/booking.py, backend/core/db.py
      НЕТ float( / Decimal / round( и нет деления «/» над денежными
      величинами (допустимы целые и целочисленное «//»);
  (б) NFR-34 — журнал append-only: во всем backend/** НЕТ
      `UPDATE transactions` и `DELETE FROM transactions` (балансы — SUM по
      журналу, записи не изменяются и не удаляются);
  (в) NFR-36 — моки без сети: в backend/wallet/** НЕТ httpx / requests /
      urlopen (эквайринг и СБП захардкожены как моки, внешних вызовов нет).

Трассировка: TC-S16-M-001 (NFR-33), TC-S16-M-002 (NFR-34),
TC-S16-M-003 (NFR-36) — rule 6 (каждый тест = требование).
"""
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]

# (а) зоны денег: домен wallet + холд-контур booking + схема/подключение БД
MONEY_SOURCES = [
    *sorted((ROOT / "backend" / "wallet").glob("*.py")),
    ROOT / "backend" / "student" / "booking.py",
    ROOT / "backend" / "core" / "db.py",
]

# деление «/» допустимо ТОЛЬКО в этих не-денежных контекстах (строки
# выверены по факту HEAD: комментарии/докстринги и не-денежные величины)
_SLASH_ALLOWED = (
    "http://", "https://",  # URL в докстрингах/комментариях
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _strip_docs_and_comments(src: str) -> str:
    """Снять докстринги и #-комментарии: гвард ловит КОД, а не тексты
    (в докстрингах дроби «копейки → ₽» допустимы)."""
    lines = []
    in_doc = False
    for line in src.splitlines():
        stripped = line.strip()
        triple = line.count('"""')
        if in_doc:
            if triple >= 1:
                in_doc = False
            continue
        if triple >= 2:
            continue  # однострочный докстринг
        if triple == 1:
            in_doc = True
            line = line[: line.index('"""')]
        line = line.split("#", 1)[0]
        lines.append(line)
    return "\n".join(lines)


# ---------------------------------------------------------------- NFR-33
def test_tc_s16_m_001_money_is_integer_arithmetic_no_float_division():
    """TC-S16-M-001 (NFR-33): в денежных модулях нет float(/Decimal/round(
    и нет деления «/» (только целые и «//»). Случайные «/» над денежными
    величинами ломают копеечную точность — гвард падает при любом
    следующем редактировании (прецедент source-inspection NFR-002)."""
    for path in MONEY_SOURCES:
        src = _strip_docs_and_comments(_source(path))
        for banned in ("float(", "Decimal", "round("):
            assert banned not in src, (
                f"{path.name}: запрещенная нецелочисленная арифметика "
                f"«{banned}» (NFR-33 — деньги только целыми копейками)")
        # «/» вне строк-URL: ни одного деления — в денежных модулях
        # деление запрещено в принципе (умножение и // достаточны:
        # net = gross × (100 − c) // 100, часы floor — design «Денежные
        # правила»)
        import re

        code_wo_strings = re.sub(r'"[^"]*"', '""', src)
        code_wo_strings = re.sub(r"'[^']*'", "''", code_wo_strings)
        # «//» (целочисленное деление) разрешен — снимаем его ПЕРВЫМ,
        # дальше любой одиночный «/» нарушает гвард
        code_wo_strings = code_wo_strings.replace("//", "")
        for line in code_wo_strings.splitlines():
            normalized = line
            for allow in _SLASH_ALLOWED:
                normalized = normalized.replace(allow, "")
            assert "/" not in normalized, (
                f"{path.name}: деление «/» в коде — разрешены только целые "
                f"и // (NFR-33): {line.strip()[:80]}")


# ---------------------------------------------------------------- NFR-34
def test_tc_s16_m_002_ledger_is_append_only_no_update_or_delete():
    """TC-S16-M-002 (NFR-34): журнал transactions — append-only. Во всем
    backend/** нет `UPDATE transactions` и `DELETE FROM transactions`;
    балансы вычисляются SUM (ledger.py), исправления — только новые
    строки (release/refund закрывают холд ровно одним движением)."""
    banned = ("UPDATE transactions", "DELETE FROM transactions")
    for path in sorted((ROOT / "backend").rglob("*.py")):
        src = _source(path)
        for snippet in banned:
            assert snippet not in src, (
                f"{path}: {snippet!r} запрещен — журнал append-only (NFR-34)")


# ---------------------------------------------------------------- NFR-36
def test_tc_s16_m_003_wallet_mocks_have_no_http_clients():
    """TC-S16-M-003 (NFR-36): эквайринг и СБП — моки без внешних вызовов.
    В backend/wallet/** нет httpx / requests / urlopen (и их импортов):
    экономика работает offline, сети в денежных контурах нет."""
    banned = ("httpx", "requests", "urlopen", "urllib.request")
    for path in sorted((ROOT / "backend" / "wallet").glob("*.py")):
        src = _source(path)
        for snippet in banned:
            assert snippet not in src, (
                f"{path.name}: сетевой клиент «{snippet}» в wallet-домене "
                f"запрещен (NFR-36 — моки без сети)")


# зоны денег существуют (страховка от переименования каталогов — гвард не
# должен молча проходить на пустом списке)
def test_money_source_files_present():
    assert any(p.name == "ledger.py" for p in MONEY_SOURCES)
    assert any(p.name == "booking.py" for p in MONEY_SOURCES)
    assert any(p.name == "db.py" for p in MONEY_SOURCES)
