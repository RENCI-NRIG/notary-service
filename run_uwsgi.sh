#!/usr/bin/env bash

APPS_LIST=(
  "admin"
  "auth"
  "contenttypes"
  "sessions"
  "users"
  "comanage"
  "projects"
  "datasets"
  "workflows"
  "nsadmin"
  "infrastructure"
  "nsmessages"
)

FIXTURES_LIST=(
  "workflowroles"
)

#APPS_LIST=()

for app in "${APPS_LIST[@]}";do
    python manage.py makemigrations $app
done
python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate

for fixture in "${FIXTURES_LIST[@]}";do
    python manage.py loaddata $fixture
done
python manage.py collectstatic --noinput

# COmanage sync on startup
python manage.py sync_on_startup

if [[ "${USE_DOT_VENV}" -eq 1 ]]; then
    uwsgi --uid ${UWSGI_UID:-1000} --gid ${UWSGI_GID:-1000}  --virtualenv ./.venv --ini ns_uwsgi.ini
else
    uwsgi --uid ${UWSGI_UID:-1000} --gid ${UWSGI_GID:-1000}  --virtualenv ./venv --ini ns_uwsgi.ini
fi
