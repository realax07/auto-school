# Покрытие: add-code-domain-folders — TC-S13-001…004

Дельта: `openspec/changes/add-code-domain-folders/specs/codebase-structure/spec.md` —
2 ADDED-требования, 4 MUST-сценария. Покрытие полное: 4/4 (кейс 1:1 на
сценарий). Принцип партии (Н5): вся поведенческая автоматизация уже
существует — полный pytest-набор (371 passed, зеркало CI), e2e (67),
NFR-инспекции исходников, матрица маршрута /js из код-ревью (review-001
§3, 13 проб TestClient); кейсы фиксируют трассировку «сценарий спеки →
автоматизация/ручной шаг» и НЕ заводят новых тестов (NFR-27 — сценарии,
needles, маркеры кейсов не менялись; review-001 §2).

Обозначения: Org = Requirement «Доменная организация кода (backend +
frontend/js)»; Ent = Requirement «Стабильные точки входа и контракт
раздачи /js/*».

| Кейс | Сценарий спеки | Автоматизация |
|---|---|---|
| TC-S13-001 | Org: «Все импорты работают после переноса» | полный набор `env -u GITHUB_EVENT_PATH pytest tests/ -q` — 371 passed (48bd504; unit 22 + api-выборка 128 + web 38 + e2e 67 подтверждены review-001 §6); смоук-импорт `from backend.app import create_app`; смоук 21 модуля без циклов — review-001 §2 |
| TC-S13-002 | Org: «Тесты правятся только механически» | ручной дифф-аудит (`git diff HEAD-before -- tests/`, сверка со списками design.md D2/D3/D4) + независимый построчный аудит review-001 §2 (каждая строка — симметричная пара old→new либо литерал/monkeypatch); grep старых функциональных ссылок — готовность 1.3; сопровождающий сигнал — зеленые наборы на границах волн |
| TC-S13-003 | Ent: «Точки входа стабильны» | `tests/test_container_contract.py` (Dockerfile/compose/CI — прогон без правок); git grep uvicorn-целей (Dockerfile:83, autoschool.service:11, run_dev.sh:9); e2e-спавн `backend.app:app` (test_ui_playwright:218, 67 passed); `tests/web/test_static.py::test_tc_reg_016_health_and_registered_page_available` + `::test_tc_reg_018_health_endpoint` (GET /api/health → 200 {"ok": true}); `docker compose build app` + `scripts/container_test.sh` — ручной приемочный шаг (задача 3.3) |
| TC-S13-004 | Ent: «Раздача /js/* из подпапок эквивалентна прежней» | матрица 13 проб TestClient — review-001 §3 (200: student/cabinet.js, shared/api.js, корневые policy.js/instructors.js; 404: ../.env, %2e%2e, //etc/passwd, .hidden, student/.env, ./cabinet.js, nope.js, старый URL admin-dashboard.js; + слэш-наблюдение) — ручные пробы, воспроизводимые на приемке; wiring `frontend_source()` — 11 вызовов/4 файла без правок (test_s4_pages_wired_to_real_api_shapes, test_dashboard_page_nav_sections_fr19, test_dashboard_page_wiring_fr18_fr20_fr22, test_cabinet_page ×5, test_instructors_cta_wiring_to_apply, test_cabinet_stub_session_guard_wiring); needle '/js/policy.js' — test_s9_policy_api_and_page_guest; e2e smoke /js/student/cabinet.js + /js/shared/api.js (задача 3.2) |

Свод по автоматизации партии: новых автотестов не добавляется —
поведенческие якоря (полный pytest-набор, container_contract, wiring
frontend_source, e2e) прогоняются без правок сценариев (NFR-27); ручные
шаги кейсов выполняются на приемке (гейт 5.1 / задача 3.4 regress-final):
дифф-аудит тестов, контейнерная верификация (сборка образа +
container_test.sh), матрица /js (13 проб TestClient). Измененные тесты
волны 1–2 — только импорт-строки/литералы путей/строковый monkeypatch/
резолв conftest-хелпера (классы A/B/C, design.md «Границы правок
тестов»); независимая сверка — review-001 (approve, 1 minor косметический
вне поведения).
