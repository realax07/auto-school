#!/bin/bash
# Запуск Auto School API (спринт-0) с env из .env
cd /home/hermes-bot/auto-school
set -a
source .env
set +a
export AUTOSCHOOL_DB_PATH=/home/hermes-bot/auto-school/data/app.db
mkdir -p data
exec /home/hermes-bot/.hermes/tools/python-3.14.7+202****0901-linux-x64/bin/python3 -m uvicorn backend.app:app --host 127.0.0.1 --port 8390
