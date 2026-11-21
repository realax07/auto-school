"""Провайдер-адаптер генерации ответов ассистента «ГигаЧат» (Спринт 19,
change add-ai-chat-home, задача 19.2.1; design.md «Решение 1»).

Контракт адаптера — generate(messages) -> reply: единственный шов
генерации. Роутер (routes.py) знает только контракт, поэтому смена
провайдера (внешний инференс) — это замена реализации ВНУТРИ backend/ai/
(set_provider / новый класс) без правок фронтенда — ограничение Заказчика
(requirements-19, «Ограничения»).

Текущий провайдер (v1, временное решение Заказчика — BACKLOG #5):
«hermes-session» — CLI `hermes chat` oneshot. Канал передачи текста —
`--query-file -` (stdin; help CLI: «Safe for arbitrary text», arch-review
001 MIN-2 / review-002): НИ текст сообщения ученика, НИ системный промпт
не идут argv — argv процесса виден в process-list хоста (ps) весь ход
генерации. Бюджет ответа (NFR ≤30 с): `--run-budget SECONDS` самого hermes
+ собственный таймаут subprocess (PROVIDER_TIMEOUT_SECONDS ≤ 30).

Системный промпт ограничивает темы (FR-19.6): ПДД, дорожные ситуации в
России, ГИБДД; опора на контент content/pdd и интернет; посторонние
вопросы — вежливый отказ без ответа по существу.

Секреты, служебные argv и тексты сообщений в логи не попадают (NFR-3):
модуль не логирует вовсе; любая неудача провайдера (таймаут, ненулевой
код, пустой ответ) наружу — ProviderError БЕЗ деталей (механика раскрыта
не будет — routes.py отдаст человеческий текст).

Параллельные вызовы провайдера сознательно НЕ ограничиваются (design.md
«Риски», MIN-3: sync-хендлер FastAPI уходит в threadpool; нагрузки
спринта малы; семафор/очередь не вводятся; поведение при параллельных
запросах на 19.4 НЕ проверяется).
"""

import re
import subprocess

# Исполняемый файл провайдера (arch-review 001 п.8: which hermes →
# /home/hermes-bot/.local/bin/hermes, oneshot-режим подтвержден).
CHAT_EXECUTABLE = "hermes"

# Внутренний бюджет hermes (--run-budget SECONDS) — ниже собственного
# таймаута: hermes обязан свернуться сам, таймаут — страховка.
_RUN_BUDGET_SECONDS = 25

# Собственный таймаут ≤30 с (NFR; design.md «Решение 1»).
PROVIDER_TIMEOUT_SECONDS = 30

# Наблюдение dev-волны 19.3: hermes chat в этом окружении печатает после
# ответа служебный хвост «session_id: …» — он НЕ часть ответа ученика.
# Срезаем от первой строки «session_id:» до конца stdout; без хвоста
# ответ не меняем (легитимная строка «session_id:» в тексте ответа
# ассистента о ПДД невозможна по системному промпту — темы ПДД/ГИБДД).
_SESSION_TAIL_RE = re.compile(r"\n*session_id:\s*\S.*$", re.DOTALL)


def _strip_session_tail(stdout: str) -> str:
    return _SESSION_TAIL_RE.sub("", stdout).strip()

# Сколько последних сообщений истории отдается провайдеру как контекст
# («последние две недели он помнит» — решение Заказчика; глубина 14 дней
# обеспечивает routes.py на выборке).
_CONTEXT_MESSAGE_LIMIT = 20

SYSTEM_PROMPT = (
    "ГигаЧат — помощник по обучению ПДД. Отвечай только по своим темам: "
    "Правила дорожного движения, дорожные ситуации в России, ГИБДД. "
    "Опирайся на учебный контент автошколы (content/pdd) и интернет. "
    "Вопросы не по этим темам — вежливо отклони, не отвечая по существу. "
    "Отвечай по-русски: кратко, понятно и дружелюбно к ученику."
)


class ProviderError(Exception):
    """Провайдер не ответил (ошибка запуска, таймаут, ненулевой код,
    пустой ответ).

    Детали (argv, stderr, тексты сообщений) сознательно не хранятся и
    не логируются — NFR-3; наружу идет только человеческий текст.
    """


def build_query(messages: list[dict]) -> str:
    """Единый текст запроса провайдеру: системный промпт + стенограмма
    диалога (messages: [{role: 'user'|'assistant', text}, ...], порядок
    хронологический; последний элемент — новое сообщение ученика).
    Заканчивается репликой-приглашением — провайдер продолжает диалог."""

    def _speaker(role: str) -> str:
        return "Ученик" if role == "user" else "ГигаЧат"

    lines = [SYSTEM_PROMPT, "", "История диалога (для контекста):"]
    for message in messages[-_CONTEXT_MESSAGE_LIMIT:]:
        lines.append(f"{_speaker(message['role'])}: {message['text']}")
    lines.append("ГигаЧат:")
    return "\n".join(lines)


class HermesSessionProvider:
    """Провайдер «hermes-session»: oneshot-вызов CLI `hermes chat`."""

    name = "hermes-session"

    def generate(self, messages: list[dict]) -> str:
        """generate(messages) -> reply (контракт design.md «Решение 1»).

        Текст запроса — в stdin (--query-file '-', мимо argv, MIN-2);
        неудача любого рода → ProviderError без деталей (NFR-3).
        """
        command = [
            CHAT_EXECUTABLE,
            "chat",
            "-Q",  # quiet: только финальный ответ (программный режим)
            "--query-file",
            "-",  # текст запроса читается из stdin — НЕ argv (MIN-2)
            "--oneshot",
            "--run-budget",
            str(_RUN_BUDGET_SECONDS),
        ]
        try:
            completed = subprocess.run(
                command,
                input=build_query(messages),
                capture_output=True,
                text=True,
                timeout=PROVIDER_TIMEOUT_SECONDS,
            )
        except subprocess.TimeoutExpired:
            raise ProviderError
        except OSError:
            # CLI недоступен (нет бинарника/прав) — та же человеческая
            # ошибка наружу, без раскрытия причины.
            raise ProviderError
        if completed.returncode != 0:
            raise ProviderError
        reply = _strip_session_tail(completed.stdout or "")
        if not reply:
            raise ProviderError
        return reply


# Активный провайдер модуля (шов замены: внешний инференс подставляется
# set_provider без правок роутера и фронтенда — design.md «Решение 1»).
_provider = HermesSessionProvider()


def set_provider(provider) -> None:
    """Замена активного провайдера (backend/ai — единственная точка)."""
    global _provider
    _provider = provider


def active_provider():
    """Текущий провайдер (для проверок/тестов; генерация — generate_reply)."""
    return _provider


def generate_reply(messages: list[dict]) -> str:
    """Единственная точка генерации для роутера: generate(messages) -> reply."""
    return _provider.generate(messages)
