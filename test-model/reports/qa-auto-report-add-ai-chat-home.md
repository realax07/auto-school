# QA-auto отчет: add-ai-chat-home (Спринт 19)

> Составлено ПМ из отчетов qa_automation (сессии 20261119_170213_c31bed + фон-прогоны)
> и собственных верификационных прогонов. Дата: 2026-11-19.

## Маппинг TC → автотесты

| TC | Кейс | Носитель |
|---|---|---|
| TC-S19-001 | 401 без валидного токена (chat/history) | tests/unit/test_s19_ai_chat.py::test_tc_s19_001_chat_without_session_unauthorized |
| TC-S19-002 | Контракт ответа {ok, reply} | tests/unit/test_s19_ai_chat.py::test_tc_s19_002 (провайдер мок) |
| TC-S19-003 | Пустая история → приветствие | tests/unit/…::test_tc_s19_003_history_empty + tests/web/test_ui_playwright.py::test_s19_home_chat_empty_history_greeting_and_composer |
| TC-S19-004 | Изоляция user_id | tests/unit/…::test_tc_s19_004_history_isolated_per_user |
| TC-S19-005/006 | Retention: старое удаляется физически / внутри окна | tests/unit/…::test_tc_s19_005/006 |
| TC-S19-007 | 422 пустое сообщение — человеческий текст | tests/unit/…::test_tc_s19_007_empty_message_422_human_text |
| TC-S19-008 | 503 провайдер — человеческий текст | tests/unit/…::test_tc_s19_008_provider_error_503_human_text |
| TC-S19-009 | Текст через stdin, мимо argv; бюджет ≤30 с | tests/unit/…::test_tc_s19_009_provider_sends_text_via_stdin_not_argv |
| TC-S19-010 | Таймаут/returncode/пустой stdout → ProviderError | tests/unit/…::test_tc_s19_010_provider_failure_modes_raise_provider_error |
| TC-S19-011 | Граница retention (14d±) детерминированно | tests/unit/…::test_tc_s19_011_retention_exact_boundary |
| TC-S19-012 | Срез служебного хвоста session_id | tests/unit/…::test_tc_s19_012_provider_strips_session_id_tail |
| TC-S19-WEB-001 | Пустая история: приветствие+композер (1440×900) | tests/web/test_ui_playwright.py::test_s19_home_chat_empty_history_greeting_and_composer |
| TC-S19-WEB-002…005 | Чат-сценарии/ошибки/«+»/«Скоро» (390px) | tests/web/test_ui_playwright.py::test_s19_home_chat_* (носители волны 19.4) |
| TC-S19-WEB-004 (десктоп) | Навигация сайдбар: instructor-choice/my-requests; инвариант BUG-060; замена решением 2026-11-18 | tests/web/test_ui_playwright.py::test_tc_ui_060_cabinet_navigation_sidebar_requests_choice (ПЕРЕПИСАН) |
| TC-S19-REG-001 | Регресс кабинета: сайдбар/таб-бар/разделы | tests/web/test_sidebar_unified.py, tests/web/test_mobile_tabbar.py, test_cabinet_page.py (переведенные гарды) |

## Неавтоматизированное (ручное)

- TC-S19-MAN-001 — боевой smoke провайдера: реальный `hermes chat -Q --query-file - --oneshot --run-budget 25` (бюджет hermes 25 с + таймаут адаптера 30 с), срез session_id на живом ответе, latency. Ручной пункт приемки ( изоляция автотестов от CLI — design Риски).

## Примечания

- Вербатим-гарды test_cabinet_page.py переведены на новые макеты (design/mocks/mobile/mobile-home-chat.html + home-chat-web.html) БЕЗ ослаблений: удаленные элементы — носители absence (count==0), wiring-гарды (/api/auth/me, X-Session-Token, logout, футер) сохранены.
- TC-UI-060 переписан на навигацию сайдбар (замена BUG-060 решением Заказчика 2026-11-18, цитата в docstring); мобильная нога навигации — НАХОДКА, ждет решения Заказчика (ОВ-4: пункты «Найти инструктора»/«Мои заявки» в таб-баре ≤760px отсутствовали и до спринта — доступ был через удаленные плитки).
- Валидационные 422 машинного шейпа {detail:[...]} (конвенция Sprint-0) — фронт обрабатывает оба шейпа (CR-19.3 MIN-3).
