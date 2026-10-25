# Code Review: add-containerization (review-001)

- Дата: 2026-10-25
- Ревьюер: code_reviewer (адверсариальный режим, AI Factory)
- Дифф: `git diff main...HEAD` — feat/s6-dev, коммит 88b6d62
- Scope: Dockerfile, docker-compose.yml, deploy/, requirements.txt, .github/, scripts/
- Задачи пакета в диффе: 1.1 (Dockerfile+.dockerignore+pin), 2.1 (compose+nginx.conf+README),
  3.1 (container_test.sh), 4.1 (CI docker-build). 2.2/5.1/5.2 — вне диффа по плану.

## Верификация (что реально прогонялось)

| Проверка | Результат |
|---|---|
| `pytest tests/test_s3_backend.py -q` (worktree, bare-metal .venv) | **43 passed** (111.7s) — совпадает с верификацией ПМ |
| pin requirements vs `pip freeze` bare-metal .venv (`/home/hermes-bot/auto-school/.venv`) | **полное совпадение** всех 6 версий: fastapi==0.143.1, uvicorn==0.54.0, bcrypt==5.0.0, python-multipart==0.0.32, pytest==9.1.1, httpx==0.28.1 |
| `git diff main...HEAD -- .github/workflows/flow.yml` | только добавление job docker-build; существующие job не тронуты |
| `git diff main...HEAD -- deploy/autoschool.service deploy/nginx-autoschool.conf` | пусто — bare-metal файлы не менялись |
| Статическая верификация compose/Dockerfile | выполнена (Docker на хосте отсутствует — runtime-прогонов стека НЕТ, см. Ограничения) |

## Ограничения ревью

Docker/compose на хосте нет: build, `compose up`, digest образов, healthcheck в рантайме
и `container_test.sh` НЕ выполнялись — по ним только статический анализ. Digest-пины
(python `a0f57064…`, nginx `1881968…`) не верифицируемы без registry-доступа —
подтверждение на стенде (задача 5.1) обязательно.

## Находки

### F-1 · MAJOR · Security · MinIO: дефолтные креды не отсечены механикой, только дисциплиной

docker-compose.yml сервис `minio` берет `MINIO_ROOT_USER/MINIO_ROOT_PASSWORD` из
env_file. Запрет minioadmin/minioadmin зафиксирован ТОЛЬКО комментарием в
.env.example и README. Если `.env` скопирован из .env.example без заполнения
MINIO_* (пустые строки env_file не разворачиваются как переменные) или строки
удалены — MinIO стартует с дефолтными minioadmin/minioadmin (релизные образы
MinIO предупреждают в логе, но не падают). Требование арх-ревью «дефолтные
запрещены» не имеет принудительного исполнения.

Эксплуатабельность сейчас ограничена (minio только в сети backend, порты не
публикуются, S3-адаптер — задача 6.3), но фокус спринта — безопасность, и
потом «поедет» в прод как есть.

Фикс (2 строки, без нового кода): интерполяция compose с обязательностью —
в сервисе minio заменить `env_file: .env` на:

```yaml
    environment:
      MINIO_ROOT_USER: ${MINIO_ROOT_USER:?MINIO_ROOT_USER обязателен (см. .env.example)}
      MINIO_ROOT_PASSWORD: ${MINIO_ROOT_PASSWORD:?MINIO_ROOT_PASSWORD обязателен (см. .env.example)}
```

`compose up` тогда падает с явной ошибкой при пустых/отсутствующих кредах.
Пустые значения `MINIO_ROOT_USER=` из .env.example интерполяцией ловятся
только если проверить на непустоту — при необходимости добавить guard в
.env.example-комментарий «строку удалить, а не оставлять пустой», либо
`env_file` оставить и добавить `required: true` (compose spec 2.24+).

### F-2 · MINOR · Security · Least privilege: minio получает чужие секреты через env_file

`env_file: .env` на сервисе minio вливает в его окружение ВСЕ переменные файла:
`ADMIN_PASSWORD_HASH`, `SECRET`, `ADMIN_USER`, `TLS_DIR`. Читаются через
`docker inspect` любым, у кого доступ к docker-сокету. Граница доверия та же,
но blast radius лишний; F-1 все равно переводит minio на `environment:` —
сделать одним патчем.

### F-3 · MINOR · Healthcheck: urlopen timeout == healthcheck timeout

`timeout: 3s` (compose и HEALTHCHECK) при `urlopen(..., timeout=3)`: python-процесс
может быть убит по healthcheck-таймауту ровно на границе собственного таймаута
urlopen — пограничные зависания дают флап unhealthy вместо честного ответа.
Фикс: urlopen timeout=2 (запас под убиение), либо healthcheck timeout: 5.
Логика корректна в остальном: endpoint /api/health существует (backend/app.py:96),
stdlib без curl (NFR-13), start_period=30s под init_db (MIN-4), дублирование
Dockerfile+compose требуется спекой — держать синхронно (сейчас синхронны).

### F-4 · MINOR · scripts/container_test.sh: абсолютный TESTS_DIR ломает монтирование

`-v "./${TESTS_DIR}:/app/tests:ro"` — при вызове с абсолютным путем получится
`./\/abs/path`. Дефолтный и CI-путь работают. Нит: нормализовать
`TESTS_DIR="$(realpath "${1:-tests}")"`. Также шаг `docker compose build app`
в CI-job дублируется со сборкой внутри скрипта — на CI это cache-hit, в
комментариях осознано; не блокер.

### F-5 · INFO · Пиннинг: digest не верифицируемы, MinIO без digest

python:3.12-slim и nginx:1.29-trixie запинены тег+digest — правильно, но digest
не проверить офлайн (см. Ограничения). MinIO — release-тег без digest; ADR-006
фиксирует это как осознанное ограничение (анонимный registry). Принимается;
рекомендация: добавить digest при появлении аутентификации, до тех пор digest
двух остальных образов подтвердить на стенде в 5.1.

### F-6 · INFO · nginx: паритет с bare-metal соблюден, но 1M-лимит загрузок наследуется

container nginx.conf повторяет bare-metal (80→443, proxy_pass, X-Forwarded-*,
заголовки). `client_max_body_size` нет в ОБОИХ конфигах — паритет есть (задача —
«эквивалент»), но дефолт nginx 1M даст 413 на загрузках документов >1MB через
80/443. Пре-существующее поведение bare-metal, вне скоупа диффа — завести как
отдельный трекинг, не чинить в этом PR.

### F-7 · INFO · design.md vs имплементация: «MinIO — свой непривилегированный образ»

minio/minio по умолчанию работает от root; `user:` в compose не задан. Либо
добавить `user:` (и проверить запись в том minio-data), либо скорректировать
формулировку design.md §Безопасность. Не блокер.

## Проверка фокуса (по брифу)

1. **Безопасность**: non-root appuser корректен (USER после COPY; /data/db,
   /data/uploads созданы до USER с chown — named volume при первом монтировании
   наследует владельца, типичная ловля обойдена). Секреты в образ не попадают:
   .dockerignore закрывает `.env*`, `deploy/tls/`, `data/`, `.git`, `.venv`,
   `__pycache__`, `tests/`; в Dockerfile их нет. Сети изолированы: nginx — только
   frontend (MIN-1), minio — только backend (NFR-16), app — обе; наружу только
   80/443; app 8390 и minio 9000/9001 не публикуются. НО: MinIO-креды без
   принудительного отсечения дефолтов (F-1, блокер) + лишние секреты в minio (F-2).
2. **Volumes**: db→/data/db, uploads→/data/uploads, minio-data→/data — named,
   переживают down/up (документировано в README, включая опасность `down -v`).
   Ручной перенос data/app.db согласован с project-name (autoschool_db). ОК.
3. **Healthcheck**: корректен по механике (см. F-3 по таймауту); endpoint
   существует; stdlib-only; start_period обоснован. compose depends_on
   nginx→app service_healthy — корректно.
4. **Pin vs локальный pytest**: все 6 версий == фактический bare-metal .venv;
   smoke `tests/test_s3_backend.py` — 43 passed. Не ломает. ОК.
5. **Bare-metal совместимость**: autoschool.service и nginx-autoschool.conf
   не тронуты (проверено диффом); bind 0.0.0.0 только аргументом CMD контейнера;
   README покрывает переключение режимов в обе стороны + конфликт портов (MIN-2)
   и INC-001. ОК.
6. **Соответствие tasks.md/design.md**: 1.1 (все пункты, включая HEALTHCHECK
   без curl и .dockerignore-набор), 2.1 (env paths, healthcheck, depends_on,
   MIN-1, README-контракт), 3.1 (read-only монтирование tests/, /tmp вне томов,
   e2e хостовой, один digest), 4.1 (additive job, build+in-image pytest) —
   соответствуют. Код backend/ и frontend/ в диффе отсутствует — контракт
   «код без изменений» соблюден.

## Вердикт

**RETURN** — один блокер:

- F-1 (MAJOR): отсечь дефолтные креды MinIO механикой compose (`${VAR:?…}`),
  попутно F-2. F-3/F-4 — желательно тем же пушем, не блокируют.
  F-5–F-7 — фиксировать/трекинг, правок в этом PR не требуют.

После F-1(+F-2) — повторное ревью только по диффу docker-compose.yml, по
остальным файлам замечаний нет. Runtime-верификация стека (build, compose up,
healthcheck, container_test.sh) остается за задачей 5.1 на Docker-стенде —
это ревью ее не заменяет.

---

## Итерация 2 · повторное ревью по диффу docker-compose.yml

- Дата: 2026-10-25
- Дифф: `git diff HEAD~1..HEAD` — коммит bbf75d1 (`.env.example` +4, `docker-compose.yml` +7/−2; больше ничего)
- Формат: только снятие F-1/F-2 из итерации 1; код не правился.

### F-1 (MAJOR, дефолтные креды MinIO) — FIXED

В сервисе `minio` добавлен блок `environment:` с интерполяцией
`${MINIO_ROOT_USER:?…}` / `${MINIO_ROOT_PASSWORD:?…}`. Механика корректна:
compose интерполирует из проекта `.env`, `:?` роняет `compose up` при
переменной не заданной ИЛИ пустой — то есть ровно сценарий «скопировал
.env.example и не заполнил / удалил строки», который был дырой итерации 1.
Дефолтные minioadmin/minioadmin отныне невозможны без явного вписывания их в
.env (а это уже не «дефолт по невниманию»). Блокеру requirements
«отсечение дефолтов механикой compose» соответствует.

Наблюдение (не блокер, фиксировать): .env.example теперь содержит непустые
плейсхолдеры `CHANGE_ME_minio_user` / `CHANGE_ME_strong_password_min`, которые
проходят `:?`-guard. Риск «стартовал с забытыми кредами» возвращается, но уже
не с публично известными дефолтами — допустимо; при желании усилить guard'ом
на префикс `CHANGE_ME` или вернуть пустые значения в .env.example (guard `:?`
их ловит).

### F-2 (MINOR, лишние секреты в окружении minio) — NOT-FIXED

`env_file: .env` на сервисе `minio` ОСТАВЛЕН (docker-compose.yml:59). Все
чужие секреты (`ADMIN_PASSWORD_HASH`, `SECRET`, `ADMIN_USER`, `TLS_DIR`) по-
прежнему вливаются в окружение контейнера minio и читаются через
`docker inspect`. Коммит-мейсседж заявляет «F-1/F-2», но дифф закрывает
только механику F-1; F-2 требовал именно уйти от env_file на minio.

Фикс — одна строка: удалить `env_file: .env` из сервиса `minio`. Это
безопасно: оба MINIO_* приходят через интерполяцию из проектного `.env`
(`environment:` при этом и так имеет приоритет над env_file), остальные
переменные minio не нужны. Сервисы `app` и `nginx` не трогать.

### Вердикт итерации 2

**RETURN** — один незакрытый finding:

| Finding | Приоритет | Статус |
|---|---|---|
| F-1 дефолтные креды MinIO | MAJOR | FIXED — `${VAR:?}` отсекает пустые/отсутствующие |
| F-2 env_file на minio | MINOR | NOT-FIXED — удалить `env_file: .env` из сервиса minio |

После удаления `env_file: .env` на minio повторное ревью не требуется — правка
механическая, закрываю APPROVE'ом по факту диффа (−1 строка). F-3–F-7 остаются
в статусе итерации 1 (желательно/трекинг). Runtime-верификация стека — по-
прежнему за задачей 5.1 на Docker-стенде.

---
МЕТА: Reviewer-Delegation: deleg_spawn202610251650321fffcc — spawned hermes chat session (role=code_reviewer, Спринт 6)
