#!/usr/bin/env python3
"""AI-мост «ГигаЧат» (хост): HTTP → CLI `hermes chat` oneshot.

Волна 19.6 change add-ai-chat-home. Боевой бэкенд-контейнер не имеет
hermes CLI; мост поднимается на ХОСТЕ и вызывает CLI как dev-провайдер.

- Слушает ТОЛЬКО docker-bridge IP (default 172.19.0.1:8790; env
  AI_BRIDGE_HOST): порт недоступен снаружи — docker-bridge IP не
  маршрутизируется с интернета (ufw off не играет: адрес приватный).
- Протокол: POST /chat, тело {"query": str} → {"reply": str};
  прочие пути/методы → 404; не-JSON/пустой query → 400.
- Текст запроса — в stdin `hermes chat` (--query-file -, мимо argv,
  arch-review 001 MIN-2); бюджет CLI --run-budget 25s (сворачивается
  сам), таймаут моста 28s — страховка; NFR ≤30s держит роутер своим
  таймаутом; SESSION_TAIL срезается тем же правилом, что в
  провайдере v1 (наблюдение dev-волны 19.3).
- Секреты/argv/тексты в логи не пишутся (NFR-3).
- Запуск: user-systemd юнит ~/.config/systemd/user/ai-bridge.service
  (`systemctl --user enable --now ai-bridge`).
"""

import json
import re
import subprocess
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os

CHAT_EXECUTABLE = "hermes"
_RUN_BUDGET_SECONDS = 25
_BRIDGE_TIMEOUT_SECONDS = 28
_BIND_HOST = os.environ.get("AI_BRIDGE_HOST", "172.19.0.1")
_BIND_PORT = int(os.environ.get("AI_BRIDGE_PORT", "8790"))

_SESSION_TAIL_RE = re.compile(r"\n*session_id:\s*\S.*$", re.DOTALL)


def _generate(query: str) -> str:
    command = [
        CHAT_EXECUTABLE, "chat",
        "-Q", "--query-file", "-", "--oneshot",
        "--run-budget", str(_RUN_BUDGET_SECONDS),
    ]
    completed = subprocess.run(
        command, input=query, capture_output=True, text=True,
        timeout=_BRIDGE_TIMEOUT_SECONDS)
    if completed.returncode != 0:
        return ""
    return _SESSION_TAIL_RE.sub("", completed.stdout or "").strip()


class Handler(BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802 (stdlib API)
        if self.path != "/chat":
            self._code(404)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(
                self.rfile.read(length).decode("utf-8") or "{}")
            if not isinstance(payload, dict):
                # MIN-2 (review-19.6-001): массив/строка/число — 400, не AttributeError
                self._code(400)
                return
            query = str(payload.get("query", "")).strip()
        except (ValueError, UnicodeDecodeError):
            self._code(400)
            return
        if not query:
            self._code(400)
            return
        try:
            reply = _generate(query)
        except (subprocess.TimeoutExpired, OSError):
            # таймаут CLI / CLI недоступен — пустой reply (NFR-3: без деталей)
            reply = ""
        body = json.dumps({"reply": reply}).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _code(self, code: int) -> None:
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def log_message(self, *args) -> None:  # NFR-3: логов нет
        pass


if __name__ == "__main__":
    ThreadingHTTPServer((_BIND_HOST, _BIND_PORT), Handler).serve_forever()
