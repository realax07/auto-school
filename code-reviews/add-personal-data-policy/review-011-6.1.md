<!-- reviewer: code_reviewer (изолированная сессия) | ре-ревью задачи 6.1 после доработки | дифф: ac5931e..86c6f5a (deploy/RUNBOOK.md) | дата: 2026-11-04 -->

# Code review (ре-ревью): задача 6.1 (change add-personal-data-policy)

Ре-ревью после доработки по вердикту return (review-007-6.1.md: 2 мажора в
deploy/RUNBOOK.md, шаг 4 «Контроль»). Дифф `git diff ac5931e..86c6f5a` —
только deploy/RUNBOOK.md (шаг 4, ~+13/−6 строк: контрольные команды через
nginx, exec-вариант 8390, диагностика через `sh -c`). Объем настоящего
ревью ограничен проверкой закрытия MAJ-1/2; arch-review.md и остальной код
не трогались.

Факты, по которым велась сверка (все — в репо на 86c6f5a):
docker-compose.yml (app: порты НЕ публикуются, environment
POLICY_FILE=/app/deploy/policy/policy.md, bind-mount :ro; nginx: ports
"80:80"/"443:443"), deploy/container/nginx.conf (listen 80/443, server_name
_, `location / → proxy_pass http://app:8390` — путь передается как есть,
/api/policy доходит до приложения), Dockerfile (python:3.12-slim pinned;
«HEALTHCHECK без curl — python stdlib уже в образе»). Docker-рантайм в
среде ревью недоступен (permission denied на docker.sock) — проверка
статическая; смок nginx на машине ревью — в «Что НЕ проверено».

## Вердикт: approve

Reviewer-Delegation: deleg-cr-20261103-policy611-external

## Закрытие замечаний review-007

### MAJ-1 (первичная контрольная команда через 8390) — ЗАКРЫТО

В редакции 86c6f5a шаг 4:
- первичные команды — через nginx: `curl -s http://127.0.0.1/api/policy`
  («с хоста, через nginx») и `curl -sk https://<host>/api/policy`
  («с внешней машины») — RUNBOOK:48–49;
- вариант 8390 перенесен в явный контейнерный вид и помечен
  «внутри контейнера»: `docker compose exec app curl -s
  http://127.0.0.1:8390/api/policy` — RUNBOOK:50; заголовок шага прямо
  говорит «порт 8390 наружу НЕ публикуется» — RUNBOOK:46;
- проверка статической страницы тоже переведена на nginx:
  `https://<host>/policy` или `http://127.0.0.1/policy` (было
  `http://127.0.0.1:8390/policy`);
- ожидаемый вывод сохранен (200 `{"ok":true,"version":"2.0",...}`, версия
  = новой `policy-version`).

Исполнимость подтверждена статически: nginx публикует 80/443
(docker-compose.yml), nginx.conf проксирует `location /` на
`http://app:8390` без переписывания пути → /api/policy достигает
приложения; выполняется с хоста стека и с внешней машины. Замечание 1 из
review-007 закрыто ровно по рекомендации.

### MAJ-2 (раскрытие $POLICY_FILE на хосте) — ЗАКРЫТО

Диагностика теперь `docker compose exec app sh -c 'head -2
"$POLICY_FILE"'` — RUNBOOK:60:
- одинарные кавычки на хосте — хост-shell переменную НЕ раскрывает
  (старая команда `cat $POLICY_FILE | head -2` удалена);
- внутри контейнера `sh -c` раскрывает `"$POLICY_FILE"` из env
  контейнера = `/app/deploy/policy/policy.md` (environment сервиса app в
  docker-compose.yml), файл существует по bind-mount :ro;
- `sh` (dash) и `head` (coreutils) входят в python:3.12-slim.
RUNBOOK:57–59 дополнительно объясняет оператору, почему раскрытие внутри
(«на хосте `$POLICY_FILE` не задана») — ровно та ловушка, которая была
замечанием 2. Замечание закрыто по рекомендации.

## Замечания

| # | Серьезность | Файл:строка | Замечание | Рекомендация |
|---|---|---|---|---|
| 1 | minor | deploy/RUNBOOK.md:50 | Контейнерный вариант использует `curl` внутри контейнера, но образ — python:3.12-slim, curl в нем отсутствует (Dockerfile сознательно строит healthcheck «без curl — python stdlib уже в образе», NFR-13). Команда вернет `exec: "curl": executable file not found in $PATH`. Не блокирует: строка — вспомогательный вариант (первичный контроль через nginx и диагностика `sh -c` исполнимы, обязательный путь оператора работает); сама рекомендация exec-curl дана была в review-007 — доработчик исполнил ее дословно | Заменить на stdlib-вариант по образцу healthcheck: `docker compose exec app python -c "import urllib.request;print(urllib.request.urlopen('http://127.0.0.1:8390/api/policy').getcode())"` — либо в одну строку сверить статус 200. Правка одной строки RUNBOOK, можно вне ревью-цикла (не блокирует approve) |

Итог: оба мажора закрыты, обязательный путь контроля операции NFR-25
(первичный curl через nginx + диагностика sh -c) исполним оператором без
разработчика. Единственное новое замечание — minor во вспомогательном
варианте, не влияет на доставляемую ценность RUNBOOK.

## Что НЕ проверено (честно)

- Docker-рантайм: `docker info` на машине ревью — permission denied на
  docker.sock, контейнерный прогон команд шага 4 не выполнялся. Все
  выводы об исполнимости — статические (compose/nginx.conf/Dockerfile),
  как и в review-007; контейнерная приемка — зона 9.1.
- Смок nginx на машине ревью (опциональный): `curl -s
  http://127.0.0.1/api/policy` → 301 (редирект на https), `curl -sk
  https://localhost/api/policy` → 404. Подтверждает только, что nginx на
  80/443 отвечает; стек s9-policy на этой машине НЕ развернут (маршрут
  /api/policy не обслуживается) — на закрытие мажоров не влияет.
- Фактическое наличие/отсутствие curl в python:3.12-slim не проверено
  эмпирически (нет доступа к docker) — замечание 1 опирается на пин
  образа в Dockerfile и его собственный комментарий «HEALTHCHECK без
  curl»; поэтому замечание оценено как minor, а не major.
