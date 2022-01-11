#!/usr/bin/env bash
set -e

source .env
virtualenv -p /usr/local/bin/python .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

chown -R ${UWSGI_UID:-1000}:${UWSGI_GID:-1000} .venv

until [ $(pg_isready -h database -q)$? -eq 0 ]; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

USE_DOT_VENV=1 ./run_uwsgi.sh

exec "$@"
