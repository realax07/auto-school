<!-- Reviewer-Delegation: deleg-s19-cr193rr2 — spawned hermes chat session (role=code_reviewer); ре-ревью тем же ревьюером | объект: фикс MIN-1 CR-19.3 (HEAD) | дата: 2026-11-19 | session: 20261119_162630_8a55d8 -->

# CR-19.3 ре-ревью (review-19.3-002) — закрытие MIN-1 review-19.3-001

Роль: code_reviewer (автор review-19.3-001). Периметр — только фикс MIN-1
(гэп композера), новое не искалось. Ревью вне flowctl: провениенс — эта
шапка + sidecar gate_runner (делает ПМ). Дерево: worktree wt-s19-ai-chat,
ветка feature/add-ai-chat-home. Объект: фикс-коммит HEAD
28de63264a5ef03792b0235657cd9846724cc3b8 «[add-ai-chat-home] ПМ: точечные
фиксы CR-19.3 MIN-1 …».

## Состав фикса

`git show HEAD --stat` → ровно 2 файла, +3/−1:

- frontend/vue/src/pages/cabinet/styles.css — 1 строка: в десктопном правиле
  `.ai-input-box` (строка 652) `gap:14px` → `gap:18px`;
- tests/unit/test_s19_ai_chat.py — +2 строки (объект ре-ревью B
  review-19.2-005, см. отдельный артефакт).

Вне этих двух файлов коммит не трогает — проверено `git show HEAD`.

## Проверки

1. Макет web: `design/mocks/home-chat-web.html`, строка 127 — `gap: 18px;`
   в `.input-box`. Десктопное правило styles.css:652 теперь `gap:18px` —
   дословное совпадение. Остальные свойства правила (background
   rgba(255,255,255,.05), border rgba(255,255,255,.14), radius 32px,
   padding 22px 14px 14px 26px, box-shadow) с макетом совпадают и коммитом
   не менялись.
2. Мобильный узел: `grep -n 'ai-input-box' styles.css` → ровно 2 gap-узла:
   652 (десктоп, 18px) и 678 (media-override ≤760px, `gap:14px`). Второй
   gap-узел в дифф не входил — мобильный оверрайд не менялся.
3. Мобильный макет: `design/mocks/mobile/mobile-home-chat.html`, строка 91 —
   `gap: 14px;` в `.input-box` → оставшиеся 14px в оверрайде совпадают с
   mobile-макетом. Аналогично совпадают radius 28px и padding
   18px 10px 12px 20px.
4. Каскад: оба правила с одинаковой специфичностью `.ai-input-box`, правило
   media ≤760px стоит позже (678 > 652) → на ≤760px побеждает мобильный
   14px. Правка только в десктопном правиле, каскад мобильного не
   пострадал; на десктопе media-правило не применяется вовсе.
5. Тесты: `/home/hermes-bot/auto-school/.venv/bin/python -m pytest
   tests/unit/test_s19_ai_chat.py -v` → **14 passed, 1 warning in 12.96s**
   (warning — StarletteDeprecationWarning из fastapi/testclient, к фиксу не
   относится).

## Замечаний нет

MIN-1 (гэп 14px вместо макетных 18px в десктопном .ai-input-box) устранён
дословно по макету; мобильный носитель не задет.

## Вердикт: approve
