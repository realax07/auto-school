#!/usr/bin/env bash
# Прогон backend-тестов ВНУТРИ того же образа, что поставляется
# (задача 3.1, MAJ-1 design.md, FR-55/NFR-17). Один digest: тесты
# доставляются read-only монтированием tests/, в образе их нет.
#
# Использование: scripts/container_test.sh [каталог-тестов, по умолч. tests]
# Требует: docker + docker compose v2.
#
# Состояние изолировано (NFR-17): AUTOSCHOOL_DB_PATH=/tmp/test.db и
# AUTOSCHOOL_UPLOADS_DIR=/tmp/uploads — временные пути в контейнерной ФС,
# вне named volumes; повторный прогон не зависит от состояния томов.
#
# e2e (playwright) остаются хостовыми — контейнерный прогон покрывает
# backend-набор (playwright-тесты скипаются importorskip: playwright в
# образе не ставится). См. deploy/container-README.md.

set -euo pipefail
cd "$(dirname "$0")/.."

TESTS_DIR="${1:-tests}"

# env_file .env обязателен для compose. Если .env нет (чистая машина) —
# временный с placeholder-значениями: креды тестов всё равно перекрываются
# ниже через -e. Файл .env в git не попадает (gitignored).
generated_env=0
if [ ! -f .env ]; then
  cat > .env <<'EOF'
ADMIN_USER=admin
ADMIN_PASSWORD_HASH=x
SECRET=container-test-secret
MINIO_ROOT_USER=container-test-user
MINIO_ROOT_PASSWORD=container-test-password
EOF
  generated_env=1
  trap '[ "$generated_env" -eq 1 ] && rm -f .env' EXIT
fi

# 1) Сборка образа (на CI слои уже в кэше — шаг дешевый)
docker compose build app

# 2) Прогон backend-набора внутри собранного образа:
#    tests/ — read-only монтирование (MAJ-1), env — переопределения
#    поверх env_file (изоляция состояния и тестовые креды)
docker compose run --rm \
  -e AUTOSCHOOL_DB_PATH=/tmp/test.db \
  -e AUTOSCHOOL_UPLOADS_DIR=/tmp/uploads \
  -e ADMIN_USER=admin \
  -e ADMIN_PASSWORD_HASH=x \
  -e SECRET=container-test-secret \
  -v "./${TESTS_DIR}:/app/tests:ro" \
  app python -m pytest /app/tests -q -p no:cacheprovider

echo "OK: backend-набор зеленый внутри образа autoschool:local (тот же digest, что поставка)"
