#!/usr/bin/env bash

python manage.py makemigrations admin
python manage.py makemigrations auth
python manage.py makemigrations contenttypes
python manage.py makemigrations sessions
python manage.py makemigrations users
python manage.py makemigrations comanage
python manage.py makemigrations
python manage.py showmigrations
python manage.py migrate
python manage.py collectstatic --noinput

if [[ "${USE_DOT_VENV}" -eq 1 ]]; then
    uwsgi --uid ${UWSGI_UID:-1000} --gid ${UWSGI_GID:-1000}  --virtualenv ./.venv --ini ns_uwsgi.ini
else
    uwsgi --uid ${UWSGI_UID:-1000} --gid ${UWSGI_GID:-1000}  --virtualenv ./venv --ini ns_uwsgi.ini
fi
