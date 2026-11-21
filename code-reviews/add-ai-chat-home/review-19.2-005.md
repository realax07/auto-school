<!-- Reviewer-Delegation: deleg-s19-cr192rr5 — spawned hermes chat session (role=code_reviewer); ре-ревью тем же ревьюером | объект: фикс MAJ-1 CR-19.2-004 (HEAD) | дата: 2026-11-19 | session: 20261119_162630_8a55d8 -->

# CR-19.2 ре-ревью (review-19.2-005) — закрытие MAJ-1 review-19.2-004

Роль: code_reviewer (автор review-19.2-004). Периметр — только фикс MAJ-1
(TC-S19-010), новое не искалось. Ревью вне flowctl: провениенс — эта шапка +
sidecar gate_runner (делает ПМ). Дерево: worktree wt-s19-ai-chat, ветка
feature/add-ai-chat-home. Объект: фикс-коммит HEAD
28de63264a5ef03792b0235657cd9846724cc3b8 «[add-ai-chat-home] ПМ: точечные
фиксы … CR-19.2-004 MAJ-1 …».

## Состав фикса

`git show HEAD --stat` → ровно 2 файла, +3/−1. Доля тестового файла: ровно
+2 строки (407–408) в test_tc_s19_010_provider_failure_modes_raise_provider_error —
после monkeypatch `subprocess.run → _FakeCompleted(returncode=1)`
восстановлены:

```python
with pytest.raises(ai_provider.ProviderError):
    provider.generate(messages)
```

Других правок в тестовом файле нет; styles.css — объект ре-ревью A
(review-19.3-002), вне периметра этого артефакта.

## Проверки

1. Сиротский monkeypatch покрыт: в TC-S19-010 все три режима сбоя теперь
   каждый завершается `pytest.raises(ai_provider.ProviderError)`:
   таймаут (строки 400–402, TimeoutExpired), returncode=1 (404–408 —
   восстановленный блок, объект MAJ-1), пустой stdout `"  \n "` (410–414).
   Прежний разрыв (патч returncode=1 без единого assert'а после себя)
   устранён.
2. Raises не вакуумный: тест зелёный, значит `provider.generate` на
   returncode=1 реально бросает ProviderError (иначе pytest упал бы с
   DID NOT RAISE).
3. Докстринг ↔ покрытие: докстринг «таймаут / ненулевой код / пустой ответ →
   ProviderError (без деталей…)» — ровно 3 режима, и в теле ровно 3 блока
   pytest.raises; расхождений нет.
4. Соседние проверки теста не задеты: NFR-3-assert «в исключении не хранятся
   детали» (`assert not ai_provider.ProviderError().args`, строка 417) на
   месте и не менялся; остальные тесты файла диффом не тронуты.
5. Регрессий нет: `/home/hermes-bot/auto-school/.venv/bin/python -m pytest
   tests/unit/test_s19_ai_chat.py -v` → **14 passed, 1 warning in 12.96s**,
   включая TC-S19-010 и провайдерные TC-S19-008/009/012 (warning —
   StarletteDeprecationWarning из fastapi/testclient, к фиксу не относится).

## Замечаний нет

MAJ-1 (потерянный pytest.raises при returncode=1 в TC-S19-010) устранён
минимальной правкой +2 строки; докстринг и остальные 13 тестов без
регрессий.

## Вердикт: approve
