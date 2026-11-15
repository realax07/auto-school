"""Unit-тесты генератора контента ПДД (Спринт 17, change add-pdd-learning,
задачи 17.2.1/17.7.2a — прецедент контрольных гейтов). Юнит-уровень
кейса TC-UI-075 (гейты целостности корпуса; нумерация TC-UI-07x —
партия QA, прецедент TC-UI-073 в tests/web/test_pdd_sections.py).

Генератор frontend/vue/scripts/generate-pdd-json.mjs — Node stdlib,
запускается subprocess на РЕАЛЬНОМ корпусе content/pdd в tmp-каталог
(PDD_OUT_DIR; корпус не трогается). Гейты целостности — провал сборки:
нарушение корпуса → ненулевой exit с именем файла/номера в stderr.

Позитив (факты корпуса, proposal «Сверка состава с фактом»):
- 26 глав правил, у каждой непустой заголовок и html-блоки;
- 8 групп / 321 знак, счётчики групп, join znaki-details по title
  (номера bijective), desc пуст ТОЛЬКО у 5.33.1/5.34.1, fine у 166;
- bilety 80×20, ровно один ✅ (correct) на вопрос, 2–5 вариантов,
  каждая ссылка изображения существует на диске (whitelist);
- shtrafi 58 строк × 3 поля;
- идемпотентность: повторный прогон — байт-в-байт те же файлы.

Негатив (мини-фикстурой на symlink-копии корпуса): сборка падает на
недостающей картинке вопроса (ссылка на несуществующий файл).
"""
import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GENERATOR = ROOT / "frontend" / "vue" / "scripts" / "generate-pdd-json.mjs"
CORPUS = ROOT / "content" / "pdd"
NODE = shutil.which("node")

pytestmark = pytest.mark.skipif(NODE is None, reason="node недоступен")


def run_generator(out_dir: Path, content_dir: Path = CORPUS) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PDD_CONTENT_DIR"] = str(content_dir)
    env["PDD_OUT_DIR"] = str(out_dir)
    return subprocess.run(
        [str(NODE), str(GENERATOR)],  # NODE не None (skipif выше)
        capture_output=True,
        text=True,
        env=env,
        timeout=300,
        cwd=str(ROOT),
    )


@pytest.fixture(scope="module")
def generated(tmp_path_factory):
    """Один прогон генератора на реальном корпусе → общий tmp-каталог."""
    out_dir = tmp_path_factory.mktemp("pdd-data")
    proc = run_generator(out_dir)
    assert proc.returncode == 0, f"генератор упал на валидном корпусе:\n{proc.stderr}"
    return out_dir


def _load(out_dir: Path, name: str):
    import json

    return json.loads((out_dir / name).read_text(encoding="utf-8"))


# --- позитив: правила -------------------------------------------------------


def test_pravila_26_chapters_with_title_and_html(generated):
    chapters = _load(generated, "pdd-pravila.json")
    assert len(chapters) == 26
    assert [c["id"] for c in chapters] == list(range(1, 27))
    for c in chapters:
        assert c["title"].strip(), f"глава {c['id']}: пустой заголовок"
        assert c["html"], f"глава {c['id']}: нет html-блоков"
        for block in c["html"]:
            assert block.startswith("<p>") and block.endswith("</p>")
            assert "<p><p>" not in block  # двойная конвертация исключена


def test_pravila_chapter10_title_from_corpus_h1(generated):
    chapters = _load(generated, "pdd-pravila.json")
    # H1 корпуса r10 — «10. Скорость движения» (заголовок = H1-блок)
    assert chapters[9]["title"].startswith("10.")
    assert "Скорость движения" in chapters[9]["title"]


# --- позитив: знаки + join znaki-details ------------------------------------


def test_znaki_8_groups_and_321_signs(generated):
    data = _load(generated, "pdd-znaki.json")
    assert [g["id"] for g in data["groups"]] == ["t1", "t2", "t3", "t4", "t5", "t6", "t7", "t8"]
    assert sum(g["count"] for g in data["groups"]) == 321
    assert len(data["signs"]) == 321
    assert [g["count"] for g in data["groups"]] == [47, 13, 38, 24, 63, 37, 22, 77]


def test_znaki_join_by_title_number_bijective(generated):
    """Join-правило design «Решение 1»: номер из title details == номерам
    group-md в ОБЕ стороны; группа знака — только из group-md."""
    details = (CORPUS / "znaki-details.json").read_text(encoding="utf-8")
    import json

    records = json.loads(details)
    data = _load(generated, "pdd-znaki.json")
    out_numbers = {s["number"] for s in data["signs"]}
    # каждый номер group-md имеет запись details с тем же номером в title
    titles = {r["title"] for r in records.values()}
    for num in out_numbers:
        assert any(t.startswith(f"Знак {num} ") for t in titles), num
    # и наоборот: записей details ровно 321 — все смэпились
    assert len(records) == 321
    # группа — из group-md (t1…t8), не из поля long записи («Предупреждающие»)
    groups_out = {s["group"] for s in data["signs"]}
    assert groups_out == {f"t{i}" for i in range(1, 9)}
    assert all(s["group"] in groups_out for s in data["signs"])


def test_znaki_desc_empty_only_allowed_numbers(generated):
    data = _load(generated, "pdd-znaki.json")
    empty = sorted(s["number"] for s in data["signs"] if s["desc"] == "")
    assert empty == ["5.33.1", "5.34.1"]


def test_znaki_fine_optional_166(generated):
    data = _load(generated, "pdd-znaki.json")
    with_fine = [s for s in data["signs"] if s["fine"]]
    assert len(with_fine) == 166
    # у 1.1 есть fine, у 5.34 — нет (пустая запись fine → null, блок не рендерится)
    by_num = {s["number"]: s for s in data["signs"]}
    assert by_num["1.1"]["fine"]
    assert by_num["5.34"]["fine"] is None


def test_znaki_images_exist_whitelist(generated, ):
    """Каждый <номер>small.png из JSON существует на диске; t8-формат
    (8.1.1 — «## | 8.1.1») распознан без pipe."""
    data = _load(generated, "pdd-znaki.json")
    by_num = {s["number"]: s for s in data["signs"]}
    assert by_num["8.1.1"]["group"] == "t8"
    assert by_num["8.1.1"]["name"] == "Расстояние до объекта"
    for s in data["signs"]:
        assert s["image"] == f"/pdd-assets/znaki/{s['number']}small.png"
        assert (CORPUS / "images" / "znaki" / f"{s['number']}small.png").is_file(), s["number"]


# --- позитив: билеты --------------------------------------------------------


def test_bilety_80_tickets_20_questions_one_correct(generated):
    index = _load(generated, "pdd-bilety-index.json")
    assert [c["id"] for c in index["categories"]] == ["abm", "cd"]
    for cat in index["categories"]:
        assert len(cat["tickets"]) == 40
        for t in cat["tickets"]:
            ticket = _load(generated, f"pdd-bilety-{t['id']}.json")
            assert ticket["id"] == t["id"]
            assert len(ticket["questions"]) == 20
            assert t["questions"] == 20
            assert t["hasImages"] == any(q["image"] for q in ticket["questions"])
            for q in ticket["questions"]:
                correct = [o for o in q["options"] if o["correct"]]
                assert len(correct) == 1, (t["id"], q["text"][:40])
                assert 2 <= len(q["options"]) <= 5
                assert "✅" not in q["options"][0]["text"]  # маркер снят с текста


def test_bilety_image_links_exist_whitelist(generated):
    """Whitelist изображений: каждая ссылка ../images/bilety/* из JSON
    существует на диске; crawl-артефакты (198 unreferenced, «none_gray.jpg?»)
    в выдачу не попадают (design «Гейты»)."""
    referenced = set()
    for nn in range(1, 41):
        for cat in ("abm", "cd"):
            ticket = _load(generated, f"pdd-bilety-{cat}-{nn:02d}.json")
            for q in ticket["questions"]:
                if q["image"] is not None:
                    assert "?" not in q["image"]
                    referenced.add(q["image"].rsplit("/", 1)[1])
    for name in referenced:
        assert (CORPUS / "images" / "bilety" / name).is_file(), name
    on_disk = {p.name for p in (CORPUS / "images" / "bilety").iterdir()}
    assert len(on_disk) > len(referenced)  # unreferenced не в JSON
    assert not any("none_gray" in name for name in referenced)


def test_bilety_abm_01_question_texts_from_corpus(generated):
    ticket = _load(generated, "pdd-bilety-abm-01.json")
    q1 = ticket["questions"][0]
    assert q1["text"].startswith("В каком случае водитель совершит вынужденную остановку?")
    assert q1["image"] is None
    assert q1["options"][1]["correct"] is True
    assert "технической неисправности" in q1["options"][1]["text"]
    assert "вынужденной остановкой" in q1["explanation"]
    q2 = ticket["questions"][1]
    assert q2["image"] == "/pdd-assets/bilety/6942508s.jpg"


# --- позитив: штрафы --------------------------------------------------------


def test_shtrafi_rows_three_fields(generated):
    rows = _load(generated, "pdd-shtrafi.json")
    assert len(rows) == 58
    for r in rows:
        assert set(r) == {"article", "violation", "penalty"}
        assert r["article"] and r["violation"] and r["penalty"]
    assert rows[0]["article"] == "Ст. 12.1"


# --- идемпотентность и манифест ---------------------------------------------


def test_rerun_is_byte_identical(tmp_path):
    """Повторный прогон идемпотентен (готовность 17.2.1)."""
    first = tmp_path / "a"
    second = tmp_path / "b"
    assert run_generator(first).returncode == 0
    assert run_generator(second).returncode == 0
    names = sorted(p.name for p in first.iterdir())
    assert names == sorted(p.name for p in second.iterdir())
    for name in names:
        h1 = hashlib.sha256((first / name).read_bytes()).hexdigest()
        h2 = hashlib.sha256((second / name).read_bytes()).hexdigest()
        assert h1 == h2, name


def test_manifest_counts_match_outputs(generated):
    manifest = _load(generated, "pdd-manifest.json")
    assert manifest["pravila"]["chapters"] == 26
    assert manifest["znaki"]["signs"] == 321
    assert manifest["znaki"]["withFine"] == 166
    assert manifest["shtrafi"]["rows"] == 58
    assert manifest["bilety"]["tickets"] == 80
    assert manifest["bilety"]["questionsPerTicket"] == 20
    for name in manifest["files"]:
        assert (generated / name).is_file(), name


# --- негатив: сборка падает на недостающей картинке (мини-фикстура) ---------


def test_build_fails_on_missing_ticket_image(tmp_path):
    """Symlink-копия корпуса (images и остальные разделы — симлинки, .md
    билетов — копии) с одной битой ссылкой → генератор завершается ошибкой,
    называя файл и имя отсутствующего изображения (spec «Сборка падает на
    недостающем изображении»)."""
    corpus = tmp_path / "corpus"
    corpus.mkdir()
    for entry in ("pravila", "znaki", "shtrafi", "images", "znaki-details.json"):
        os.symlink(CORPUS / entry, corpus / entry)
    (corpus / "bilety").mkdir()
    broken = None
    for cat in ("abm", "cd"):
        src_cat = CORPUS / "bilety" / cat
        dst_cat = corpus / "bilety" / cat
        dst_cat.mkdir()
        for md in sorted(src_cat.glob("*.md")):
            target = dst_cat / md.name
            if broken is None and cat == "abm" and md.name == "bilet-01.md":
                text = md.read_text(encoding="utf-8").replace(
                    "../images/bilety/6942508s.jpg", "../images/bilety/definitely_missing.jpg"
                )
                target.write_text(text, encoding="utf-8")
                broken = target
            else:
                os.symlink(md, target)
    assert broken is not None
    out_dir = tmp_path / "out"
    proc = run_generator(out_dir, content_dir=corpus)
    assert proc.returncode != 0
    combined = proc.stdout + proc.stderr
    assert "bilet-01.md" in combined
    assert "definitely_missing.jpg" in combined
    assert not out_dir.exists() or not any(out_dir.iterdir())  # dist не собирается
