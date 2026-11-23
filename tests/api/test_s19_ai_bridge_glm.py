"""TC-S19-011/012 (change add-ai-chat-home, волна 19.7): AI-мост v2
(services/ai-bridge/app.py) — GLM chat-completions + RAG-lite по канону
content/pdd.

Проверяется: контракт /chat {query}→{reply}; подмешивание канона ПДД в
системный промпт (RAG-lite по словам запроса); ошибки GLM любого рода
(сеть/HTTP/не-JSON/пустой content) → {"reply": ""} с 200 — провайдер
бэкенда отдаст человеческий текст (ProviderError), NFR-3 без деталей.
GLM API мокается локальным HTTP-сервером (hermetic, без сети).
"""

import importlib.util
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

MODULE_PATH = "/home/hermes-bot/auto-school/services/ai-bridge/app.py"


def _load_module(glm_url: str, content_dir: str):
    """Загрузка модуля моста с подменой env (импорт из services/ вне
    пакетной раскладки — spec.from_file_location)."""
    import os
    os.environ["GLM_API_KEY"] = "test-key-not-a-secret-fixture"
    os.environ["GLM_BASE_URL"] = glm_url
    os.environ["GLM_MODEL"] = "glm-test"
    os.environ["CONTENT_DIR"] = content_dir
    spec = importlib.util.spec_from_file_location("ai_bridge_glm", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _fake_glm(handler_body: bytes, seen: dict):
    class Fake(BaseHTTPRequestHandler):
        def do_POST(self):  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            seen["request"] = json.loads(self.rfile.read(length))
            seen["auth"] = self.headers.get("Authorization", "")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            data = handler_body
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, *args):  # NFR-3
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Fake)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _bridge(module, host, port):
    server = module.ThreadingHTTPServer((host, port), module.Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server


def _post(url: str, body: dict, timeout: int = 10):
    import urllib.request
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.status, json.loads(response.read())


@pytest.fixture()
def content_dir(tmp_path):
    """Мини-канон ПДД: два .md с разными темами + не-md (игнор)."""
    znaki = tmp_path / "znaki"
    znaki.mkdir()
    (znaki / "t3_zapret.md").write_text(
        "Знак 3.20 Обгон запрещён: белый круг, красная окантовка, "
        "два автомобиля.\n", encoding="utf-8")
    shtrafi = tmp_path / "shtrafi"
    shtrafi.mkdir()
    (shtrafi / "s12_speed.md").write_text(
        "Штраф за превышение скорости: от 500 рублей до лишения прав.\n",
        encoding="utf-8")
    (tmp_path / "readme.txt").write_text(
        "знак обгон штраф — не-индексируемый формат\n", encoding="utf-8")
    return str(tmp_path)


def test_tc_s19_011_bridge_glm_contract_and_rag_context(content_dir):
    """TC-S19-011: /chat {query}→{reply}; слова запроса выбирают файл
    канона (RAG-lite), фрагмент попадает в system-prompt GLM; ответ GLM
    возвращается ученику. Tracing: impact 19.7, FR-19.5/19.6."""
    seen: dict = {}
    glm_body = json.dumps({
        "choices": [{"message": {"content": "Знак 3.20 — обгон запрещён."}}]
    }).encode("utf-8")
    glm = _fake_glm(glm_body, seen)
    module = _load_module(
        f"http://127.0.0.1:{glm.server_port}/v4", content_dir)
    bridge = _bridge(module, "127.0.0.1", 0)
    try:
        status, payload = _post(
            f"http://127.0.0.1:{bridge.server_address[1]}/chat",
            {"query": "Какой знак запрещает обгон?"})
        assert status == 200
        assert payload["reply"] == "Знак 3.20 — обгон запрещён."
        # GLM вызван с моделью/ключом
        assert seen["request"]["model"] == "glm-test"
        assert seen["auth"] == "Bearer test-key-not-a-secret-fixture"
        # RAG-lite: канон знака в system, штрафной файл — не в топе
        system = seen["request"]["messages"][0]["content"]
        assert "ГигаЧат" in system
        assert "3.20" in system
        assert "Лишения прав" not in system
        # текст ученика — в user
        assert "обгон" in seen["request"]["messages"][1]["content"]
    finally:
        bridge.shutdown()
        glm.shutdown()


def test_tc_s19_012_bridge_glm_errors_empty_reply(content_dir):
    """TC-S19-012: ошибки GLM любого рода — HTTP-не-200, не-JSON,
    пустой content, недоступный GLM — мост отвечает 200 {"reply": ""}
    (человеческий текст отдаст провайдер бэкенда). NFR-3 без деталей."""
    cases = {
        "http500": (b"oops",),
        "notjson": (b"not-json",),
    }
    for name, (body,) in cases.items():
        seen: dict = {}
        glm = _fake_glm(body, seen)
        module = _load_module(
            f"http://127.0.0.1:{glm.server_port}/v4", content_dir)
        bridge = _bridge(module, "127.0.0.1", 0)
        try:
            status, payload = _post(
                f"http://127.0.0.1:{bridge.server_address[1]}/chat",
                {"query": "вопрос"})
            assert status == 200, name
            assert payload["reply"] == "", name
        finally:
            bridge.shutdown()
            glm.shutdown()
    # недоступный GLM (порт никто не слушает)
    module = _load_module("http://127.0.0.1:9/v4", content_dir)
    bridge = _bridge(module, "127.0.0.1", 0)
    try:
        status, payload = _post(
            f"http://127.0.0.1:{bridge.server_address[1]}/chat",
            {"query": "вопрос"})
        assert status == 200
        assert payload["reply"] == ""
    finally:
        bridge.shutdown()


def test_tc_s19_013_bridge_bad_requests(content_dir):
    """TC-S19-013: прочие пути → 404; пустой query / не-dict → 400
    (гигиена входа, review-19.6 MIN-2 наследуется)."""
    module = _load_module("http://127.0.0.1:9/v4", content_dir)
    bridge = _bridge(module, "127.0.0.1", 0)
    try:
        base = f"http://127.0.0.1:{bridge.server_address[1]}"
        import urllib.request
        request = urllib.request.Request(
            base + "/other", data=b"{}", method="POST")
        with pytest.raises(Exception):
            urllib.request.urlopen(request, timeout=5)
        status, _ = _post_ok_or_error(base + "/chat", {"query": "  "})
        assert status == 400
        request = urllib.request.Request(
            base + "/chat", data=b"[1,2]",
            headers={"Content-Type": "application/json"}, method="POST")
        with pytest.raises(Exception):
            urllib.request.urlopen(request, timeout=5)
    finally:
        bridge.shutdown()


def _post_ok_or_error(url: str, body: dict, timeout: int = 10):
    """POST, возвращающий (status, payload) и для ошибочных кодов."""
    import urllib.request, urllib.error
    request = urllib.request.Request(
        url, data=json.dumps(body).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return response.status, json.loads(response.read())
    except urllib.error.HTTPError as error:
        return error.code, {}
