#!/usr/bin/env bash
set -e

virtualenv -p /usr/local/bin/python .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

until [ $(pg_isready -h database -q)$? -eq 0 ]; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - continuing"

USE_DOT_VENV=1 ./run_uwsgi.sh

exec "$@"
