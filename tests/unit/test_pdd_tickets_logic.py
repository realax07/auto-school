"""Unit-тесты чистой логики секций ПДД (Спринт 17, change
add-pdd-learning, задача 17.5.2 — «unit логики тренажёра: фиксация
однократная, счёт, авто-финиш таймера — чистые функции компонента»;
плюс поиск «Штрафов» 17.6.2). Юнит-уровень кейса TC-UI-074 (тренажёр:
таймер/однократная фиксация/счёт; нумерация TC-UI-07x — партия QA,
прецедент TC-UI-073 в tests/web/test_pdd_sections.py).

Носитель логики — frontend/vue/src/pages/cabinet/sections/pdd-logic.mjs
(Vue-независимый модуль, статически импортируется lazy-чанками
PddTickets.vue/PddFines.vue). Прогон — node + harness
tests/unit/fixtures/pdd_logic_harness.mjs (Node stdlib, БЕЗ новых
зависимостей — бюджетное правило репозитория); assert-провал harness
→ ненулевой exit → падение теста. Vue-компонент не требуется.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
LOGIC = ROOT / "frontend" / "vue" / "src" / "pages" / "cabinet" / "sections" / "pdd-logic.mjs"
HARNESS = ROOT / "tests" / "unit" / "fixtures" / "pdd_logic_harness.mjs"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(
    NODE is None or not LOGIC.is_file(), reason="node недоступен"
)


def test_pdd_logic_pure_functions_harness():
    """Таймер (формат/шаг/авто-финиш), фиксация ответа ОДНОКРАТНАЯ,
    счёт верных/ошибок, статусы сетки 1–N, клиентский поиск штрафов —
    все чистые функции через harness (см. сценарии в .mjs)."""
    proc = subprocess.run(
        [str(NODE), str(HARNESS), str(LOGIC)],
        capture_output=True,
        text=True,
        timeout=60,
        cwd=str(ROOT),
    )
    assert proc.returncode == 0, f"harness упал:\n{proc.stdout}\n{proc.stderr}"
    assert "все проверки пройдены" in proc.stdout, proc.stdout
