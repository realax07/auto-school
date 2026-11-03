# Образ auto-school (ADR-006, задача 1.1): окружение — артефакт репозитория
# (урок INC-001). Multi-stage: frontend-builder собирает Vue/Vite dist
# (Спринт 9, ADR-008), venv — в builder, в runtime переносится COPY --from;
# запуск от non-root appuser (NFR-11).
#
# Сборка: docker build -t autoschool .

ARG NODE_IMAGE=node:22-slim@sha256:4b150b48b4116e2a22f2c39cc27025fbf4f153e2078fd3b14d159fdb5c7279da
ARG PYTHON_IMAGE=python:3.12-slim@sha256:a0f57064cbdcd6285fa45f51237ab0b35ea8ebaed06a1f5973e89e19dfb86704

# --- frontend-builder: сборка Vue/Vite в dist (Спринт 9, ADR-008, задача
# 2.2): node builder-этап ПЕРЕД python builder (наследование multi-stage
# ADR-006, образ pinned). Layer-cache по манифестам: package*.json копируются
# и ставятся отдельно от исходников. bare-metal (FR-57): перед деплоем
# выполняется ТОТ ЖЕ порядок из frontend/vue/ — `npm ci && npm run build`
# (артефакт dist идентичен сборке в образе; отдельного entrypoint/механики
# нет). node_modules и dev-зависимости в прод-образ не попадают.
FROM ${NODE_IMAGE} AS frontend-builder
WORKDIR /app
COPY frontend/vue/package.json frontend/vue/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY frontend/vue/ .
RUN npm run build

# --- builder: зависимости в изолированный venv ---
FROM ${PYTHON_IMAGE} AS builder
ENV PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# --- runtime: прод-чистый образ (без .env/tls/data/tests — .dockerignore) ---
FROM ${PYTHON_IMAGE}

# non-root: каталоги точек монтирования создаются заранее с владельцем
# appuser — named volume при первом монтировании наследует права
# (иначе root-владелец тома ломает non-root)
RUN useradd --create-home appuser \
    && mkdir -p /data/db /data/uploads \
    && chown -R appuser:appuser /data

WORKDIR /app
COPY --from=builder /opt/venv /opt/venv
COPY backend/ backend/
COPY frontend/ frontend/
# Собранный фронт каркаса Vue — из node builder-этапа (Спринт 9, ADR-008);
# локальный dist исключен .dockerignore — в образе артефакт сборки образа.
COPY --from=frontend-builder /app/frontend/vue/dist ./frontend/vue/dist
COPY design/ design/
COPY .env.example .env.example
COPY requirements.txt .

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1

USER appuser

EXPOSE 8390

# HEALTHCHECK без curl — python stdlib уже в образе (NFR-13).
# start_period=30s — запас на init_db (lifespan) при холодном старте
# на большом томе (задача 1.1, MIN-4)
HEALTHCHECK --interval=10s --timeout=3s --start-period=30s --retries=5 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8390/api/health', timeout=3).status == 200 else 1)"]

# Порт 8390 — тот же, что в systemd-юните (FR-57); bind 0.0.0.0 —
# аргумент CMD, не код. Миграции выполняет init_db через lifespan —
# отдельный entrypoint не вводится.
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8390"]
