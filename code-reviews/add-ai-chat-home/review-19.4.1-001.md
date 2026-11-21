<!-- Reviewer-Delegation: deleg-d255c92a8b5140a6aaaa3749ed90d27f — flowctl code_reviewer стадия, accepted | дата: 2026-11-19 | session: cli-pid 204796 (spawn-ledger; id CLI-сессии изнутри сессии недоступен) -->

# Review-19.4.1-001 — верификация 19.4.1: чек-лист + кейсы + автоматизация (Спринт 19, add-ai-chat-home)

Роль: code_reviewer, flow=1, task=19.4.5 (финальные bindings подзадач QA
перед подписью спринта). Объект — задача 19.4.1 (носители/кейсы): перевод
гардов «Главной»-чата на утвержденные макеты, approved-партия кейсов,
маппинг-отчет. Автором артефактов волны не являюсь. Worktree
wt-s19-ai-chat, ветка feature/add-ai-chat-home, HEAD на момент ревью
f8788dea62eb9d4d239e0fc7050d72992b435165. Гигиена: писан только этот
артефакт и парный review-19.4.3-001.md (зона делегации); код/тесты/спеки
не правились; push нет.

## Машинная верификация (собственные прогоны на HEAD f8788de)

1. Носители статического кабинета:
   `python -m pytest tests/web/test_cabinet_page.py -q` → `7 passed in 0.05s`.
   - Макеты-эталоны подключены путями (строки 66–67): MOCKUP_MOBILE =
     design/mocks/mobile/mobile-home-chat.html, MOCKUP_WEB =
     design/mocks/home-chat-web.html; фрагменты сверяются ПАРАМИ
     «макет ↔ страница» и «макет ↔ styles.css» дословно
     (chat_common 174–187, chat_pairs 190–201, css_pairs 205–231 — база
     веб-макета, переопределения мобилки; прогон это подтверждает).
   - Absence-носители удаленных по решению Заказчика 2026-11-18 блоков —
     строки 115–136: .greet/.assistant/.quick/.services-title/.tiles,
     id="tile-instructor"/"tile-requests", тег «В КАБИНЕТЕ», плиточные
     тексты; плюс носитель удаления мертвого wiring заглушек —
     `assert "alert(" not in html` (строка 268).
   - Wiring-гарды сохранены без ослаблений (строки 279–318): auth/me +
     X-Session-Token + sessionStorage, 401-редирект, подстановка ФИО,
     logout-флоу; живые якоря композера #ai-input/#ai-send/#ai-plus
     (272–273).

2. E2E-носители: `python -m pytest tests/web/test_ui_playwright.py -q` →
   `94 passed in 199.54s` (полный файл, 94 collected).
   - TC-UI-060 переписан (def на строке 4772, commit c6db641): навигация
     через САЙДБАР («Выбрать инструктора» → /instructor-choice, «Мои
     заявки» → #sec-requests, хеш #/my-requests, активная кнопка .on);
     цитата решения Заказчика 2026-11-18 в docstring дословно («Да,
     убираем все кнопки…»); инвариант BUG-060 сохранен отсутствием
     плиток/тега. Мобильная нога (таб-бар ≤760px) — задокументированная
     НАХОДКА ОВ-4 (в таб-баре 5 табов, пунктов нет; вопрос ПМ/СА),
     НЕ носитель — соответствует отчету маппинга
     test-model/reports/qa-auto-report-add-ai-chat-home.md, строка 33.
   - Новые носители chat — 5 × test_s19_home_chat_* (строки 4823, 4881,
     4926, 4957, 4981): приветствие/композер пустой истории, отправка с
     пузырями, история переживает reload, «+» неактивна с «Скоро»,
     мобильная геометрия 390×844.
   - Примечание среды (не finding по коду): запуск playwright на этом
     хосте требует LD_LIBRARY_PATH=/home/hermes-bot/.cache/pw-libs/root/
     usr/lib/x86_64-linux-gnu (9 общих библиотек chromium; без них
     BrowserType.launch падает по libatk). Precondition окружения
     воспроизводит прогоны QA-волны.

3. API-носитель 19.2.5: `python -m pytest tests/api/test_s19_ai_chat.py -q`
   → `12 passed, 1 warning in 12.13s` (commit d6e85b5). Трассировка в
   docstring: TC-S19-001…008 покрывают доступ/контракт/историю/изоляцию/
   retention/границы окна/ошибки валидации и провайдера; TC-S19-009/010/
   012 и 011 (граница ±1 с) остаются юнит-ногой tests/unit/test_s19_ai_chat.py;
   TC-S19-MAN-001 — ручной smoke; ссылка на approved-партию кейсов.

4. Кейсы: review-002-cases = code-reviews/add-ai-chat-home/review-19.4-002.md,
   вердикт approve (строка 78); approved-партия verbatim (ef687c7) + запись
   «одобрить» review-003-cases (de3d29a). Партия на диске:
   test-model/approved/add-ai-chat-home/ — checklist.md + TC-S19-API-001,
   TC-S19-MAN-001, TC-S19-REG-001, TC-S19-UNIT-001, TC-S19-WEB-001…005
   (10 файлов). Маппинг-отчет есть:
   test-model/reports/qa-auto-report-add-ai-chat-home.md (9cbcec9).

5. Спеки: `openspec validate --all --strict` → `Totals: 28 passed,
   0 failed (28 items)`.

Замечания уровня MAJ/BLK: нет. Замечания уровня MIN: нет (примечание
среды из п.2 — вне кода, зафиксировано для воспроизводимости).

## Вердикт: approve

Задача 19.4.1 подтверждена: носители переведены на утвержденные макеты
(ca2a8c4/c6db641/d6e85b5), absence-носители и wiring-гарды на месте,
кейс-база approved (review-002-cases approve + партия verbatim + запись
«одобрить»), маппинг-отчет присутствует. Binding 19.4.1 принимается,
спринт может подписываться.
