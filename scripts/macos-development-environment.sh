#!/usr/bin/env bash

# deployment variables
NS_HOST=127.0.0.1
NS_PORT=8443

echo "### Deploy Notary Service to: ${NS_HOST}:${NS_PORT} ###"
echo "### NOTE: This script is specific to macOS development using virtualenv ###"

# Setup environment to run notary-service

# run from top level of repository
echo "INFO: check starting directory"
if [[ $(pwd | rev | cut -d '/' -f1 | rev) == 'scripts' ]]; then
  cd ../
fi

# generate environment settings if they do not exist
echo "INFO: create base/.env if it does not exist"
if [[ ! -e base/.env ]]; then
  cp base/env.template base/.env
fi
echo "INFO: create base/secrets.py if it does not exist"
if [[ ! -e base/secrets.py ]]; then
  cp base/secrets.py.template base/secrets.py
fi
echo "INFO: create .env if it does not exist"
if [[ ! -e .env ]]; then
  cp env.template .env
fi

# check for postgres directories
echo "INFO: create pg_data/data directory if it does not exist"
if [[ ! -d pg_data/data ]]; then
  mkdir -p pg_data/data
fi
echo "INFO: create pg_data/logs directory if it does not exist"
if [[ ! -d pg_data/logs ]]; then
  mkdir -p pg_data/logs
fi

# check for neo4j directories
echo "INFO: create neo4j/data directory if it does not exist"
if [[ ! -d neo4j/data ]]; then
  mkdir -p neo4j/data
fi
echo "INFO: create neo4j/imports directory if it does not exist"
if [[ ! -d neo4j/imports ]]; then
  mkdir -p neo4j/imports
fi
echo "INFO: create neo4j/logs directory if it does not exist"
if [[ ! -d neo4j/logs ]]; then
  mkdir -p neo4j/logs
fi

# check for kafka directory
echo "INFO: create kafka directory if it does not exist"
if [[ ! -d kafka ]]; then
  mkdir -p kafka
fi

# check for safe/imports directory
echo "INFO: create kafka directory if it does not exist"
if [[ ! -d safe/imports ]]; then
  mkdir -p safe/imports
fi

# check for nginx configuration
echo "INFO: create nginx/default.conf if it does not exist"
if [[ ! -e nginx/default.conf ]]; then
  cp nginx/default.conf.template nginx/default.conf
  # replace first FQDN_OR_IP with domain
  sed -i '0,/FQDN_OR_IP/{s/FQDN_OR_IP/'${NS_HOST}'/}' nginx/default.conf
  # replace subsequent FQDN_OR_IP with domain:port
  sed -i 's/FQDN_OR_IP/'${NS_HOST}':'${NS_PORT}'/' nginx/default.conf
  sed -i 's/    server unix.*/    #server unix:\/\/\/code\/base.sock; # UNIX file socket/' nginx/default.conf
  sed -i 's/    #server host.docker.*/    server host.docker.internal:8000; # TCP socket/' nginx/default.conf
fi

# update ns_uwsgi.ini
echo "INFO: update ns_uwsgi.ini for use on port 8000"
sed -i 's/;socket = :8000/socket = :8000/' ns_uwsgi.ini
sed -i 's/uwsgi-socket        = .\/base.sock/;uwsgi-socket        = .\/base.sock/' ns_uwsgi.ini
sed -i 's/chmod-socket        = 666/;chmod-socket        = 666/' ns_uwsgi.ini

# check for virtualenv
echo "INFO: create virtualenv as venv if it does not exist"
if [[ ! -d venv ]]; then
  virtualenv -p $(which python3) venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
fi

# start database, neo4j and nginx if they are not running
source base/.env
echo "INFO: start database container"
if [[ ! $(docker-compose ps | grep database) ]]; then
  docker-compose up -d database
fi
echo "INFO: start neo4j container"
if [[ ! $(docker-compose ps | grep neo4j) ]]; then
  docker-compose up -d neo4j
fi
echo "INFO: start nginx container"
if [[ ! $(docker-compose ps | grep nginx) ]]; then
  docker-compose up -d nginx
fi
echo "INFO: start zookeeper container"
if [[ ! $(docker-compose ps | grep zookeeper) ]]; then
  docker-compose up -d zookeeper
fi
echo "INFO: start kafka container"
if [[ ! $(docker-compose ps | grep kafka) ]]; then
  docker-compose up -d kafka
fi
echo "INFO: start safe container"
if [[ ! $(docker-compose ps | grep safe) ]]; then
  docker-compose up -d safe
fi
echo "END: macos-development-environment.sh is done"

exit 0;