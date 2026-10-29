# Tasks: add-containerization

Правила: задача атомарна (одна сессия = одна задача); `[P]` — независимая
задача (параллелится, каждая в своем worktree; пишут против контрактов
design.md, не против кода друг друга). Код backend/ и frontend/ — БЕЗ
ИЗМЕНЕНИЙ (контейнеризация не меняет поведение приложения; исключение —
точечный фикс жесткого пути с тестом, если dev его вскроет). Детальные
контракты — design.md настоящего пакета. Требования —
docs/ba/requirements-containerization.md (FR-51…FR-57, NFR-11…NFR-17).

## 1. Образ приложения

- [ ] 1.1 [P] Dockerfile + .dockerignore — multi-stage: builder
      (python:3.12-slim pinned, venv /opt/venv, pip install -r
      requirements.txt) + runtime (та же база, COPY --from=builder
      /opt/venv, backend/ + frontend/); non-root appuser (каталоги
      /data/db, /data/uploads — владелец appuser); HEALTHCHECK на
      /api/health через python stdlib (без curl); CMD uvicorn
      backend.app:app --host 0.0.0.0 --port 8390; .dockerignore: .env*,
      deploy/tls/, data/, .git, .venv, __pycache__.
      tests/ в образ НЕ копируются (доставка тестов — read-only
      монтирование при прогоне, задача 3.1 — решение MAJ-1 design.md);
      HEALTHCHECK задает start_period с запасом на init_db при холодном
      старте на большом томе (значение — за dev, остальное по умолчанию;
      MIN-4).
      ПЕРЕД кодом: pin версий requirements.txt (fastapi, uvicorn,
      bcrypt, python-multipart; dev-группа pytest, httpx) — версии
      фактически установленные в .venv, чтобы контейнер совпал с
      bare-metal рантаймом.
      Готовность: docker build проходит; контейнер стартует от non-root
      (docker inspect USER); /api/health отвечает 200; HEALTHCHECK
      healthy; в образе нет .env/tls/data/tests; requirements.txt — с версиями.
      FR: FR-51, FR-54. NFR: NFR-11, NFR-12, NFR-13, NFR-14.
      Типы: [infra][tests]. Зависит от: —.

## 2. Compose-стек

- [ ] 2.1 [P] docker-compose.yml + deploy/container/nginx.conf +
      deploy/container-README.md — сервисы app (env_file .env;
      environment AUTOSCHOOL_DB_PATH=/data/db/app.db,
      AUTOSCHOOL_UPLOADS_DIR=/data/uploads; volumes db, uploads; без
      публикуемых портов; healthcheck), nginx (pinned образ; TLS и
      конфиг — монтирования; ports 80/443; depends_on app
      service_healthy), minio (pinned образ; root-креды из env_file;
      volume minio-data; порт не публикуется); сети frontend/backend;
      nginx.conf — эквивалент deploy/nginx-autoschool.conf (80→443,
      proxy_pass app:8390, X-Forwarded-*); nginx — только сеть frontend
      (не backend — MIN-1); README: оба режима деплоя (compose /
      bare-metal systemd), где секреты и тома, процедура переключения
      режимов в ОБЕ стороны (bare-metal → compose: остановка
      deploy/autoschool.service и host nginx, затем compose up; обратно:
      compose down → рестарт юнита и nginx — иначе конфликт портов
      80/443/8390; MIN-2), судьба существующей data/app.db: compose
      стартует с пустым томом, bare-metal данные в data/ не трогаются,
      ручной перенос — опциональная процедура в README (решение СА,
      design.md); предупреждение INC-001.
      Готовность: compose up поднимает стек; через nginx доступен лендинг
      и /api/health; down/up — записи БД и файлы загрузок сохраняются
      (проверка томов); `ss -tlnp` на хосте — слушаются только 80/443;
      docker compose ps — app healthy.
      FR: FR-52, FR-54, FR-57. NFR: NFR-14, NFR-15, NFR-16.
      Типы: [infra][tests][docs]. Зависит от: 1.1 (контракт образа:
      имена каталогов /data/*, порт, USER — по design.md при
      параллельности).

- [ ] 2.2 [P] Проверка idempotent-старта на существующей БД — тестовая
      процедура (в задачу 2.1/4.1 входит проверкой, здесь — явный шаг
      dev): поднять стек на томе с БД предыдущего состояния, рестарт
      контейнера ×2; init_db/lifespan доводит схему без ошибок и потери
      данных; фиксирование результата в отчете задачи.
      Готовность: рестарт на несвежем томе — старт без ошибок, данные
      целы (описанный в отчете сценарий + вывод curl /api/health).
      FR: FR-53. NFR: NFR-15. Типы: [tests][migration]. Зависит от: 2.1.

## 3. Тесты в контейнере

- [ ] 3.1 [P] scripts/container_test.sh + README-раздел — прогон
      backend-тестов ВНУТРИ того же образа: docker compose run --rm
      -v ./tests:/app/tests:ro app python -m pytest tests/ -q — тесты
      доставляются read-only монтированием на время прогона, в образе
      их нет (решение MAJ-1 design.md); с переопределением
      AUTOSCHOOL_DB_PATH=/tmp/test.db, AUTOSCHOOL_UPLOADS_DIR=/tmp/uploads
      (вне named volumes — изоляция состояния); e2e остается хостовым
      (зафиксировать в README). Требование к образу: тесты и поставка —
      один digest (никакого отдельного test-образа).
      Готовность: скрипт на чистой машине дает полный зеленый прогон
      backend-набора в контейнере; повторный прогон не зависит от
      состояния томов.
      FR: FR-55. NFR: NFR-17. Типы: [tests][infra][docs]. Зависит от: 1.1.

## 4. CI

- [ ] 4.1 [P] .github/workflows/flow.yml — новый job: setup Buildx →
      docker build образа → прогон pytest внутри собранного образа той
      же командой, что задача 3.1 (compose run с read-only монтированием
      tests/, временная БД — механика scripts/container_test.sh);
      failure сборки/тестов красит PR; существующие job без изменений.
      Готовность: на PR с ломающим Dockerfile и на PR с падающим тестом
      CI красный (проверить оба пути); на чистом PR — зеленый, шаги
      сборки и контейнерных тестов видны в логе.
      FR: FR-56. Типы: [infra][tests]. Зависит от: 1.1, 3.1.

## 5. Сборка и приемка

- [ ] 5.1 Стенд-верификация полного контура (не [P]: интеграция всех
      контрактов): на чистом каталоге — build → compose up → smoke
      (лендинг, регистрация, /api/health, загрузка файла) → down/up →
      данные целы; переключение режимов: bare-metal systemd продолжает
      работать после pull (FR-57, ноль правок кода); отчет о прогоне.
      Готовность: все проверки из design.md «План тестовых прогонов»
      выполнены, выводы команд в отчете.
      FR: FR-51…FR-57. NFR: NFR-11…NFR-17. Типы: [tests][infra].
      Зависит от: 1.1, 2.1, 2.2, 3.1, 4.1.

- [ ] 5.2 Документация и трассировка: sdd.md (раздел «Спринт 6»:
      контур, решения design.md), проверка трассировки FR/NFR по всем
      задачам, подготовка приемки (6.5 PLAN).
      Готовность: sdd.md дополнен; трассировка полная (каждый FR/NFR —
      задача/тест); ревью/приемка запланированы.
      Типы: [docs]. Зависит от: 5.1.

## Рекомендации к нарезке

- Параллелятся [P]: 1.1, 3.1 (после 1.1 — контракт образа), 4.1.
- НЕЛЬЗЯ делить: 2.1 (compose+nginx.conf+README — одна зона файлов);
  5.1 — только после всех.
- Общая зона: requirements.txt (pin версий в 1.1) — другие задачи его
  не трогают.
- Прогоны тестов — 3 набора (design.md): контейнер-тесты (3.1/4.1),
  smoke compose (2.1/5.1), полный хостовый pytest + e2e (как сейчас) —
  по одному раннеру на набор.
