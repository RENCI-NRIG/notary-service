#!/usr/bin/env bash

# Setup environment to run notary-service

# run from top level of repository
if [[ $(pwd | rev | cut -d '/' -f1 | rev) == 'scripts' ]]; then
  cd ../
fi

# generate environment settings if they do not exist
if [[ ! -e base/.env ]]; then
  cp base/dummy.env base/.env
fi
if [[ ! -e base/dummy_secrets.py ]]; then
  cp base/dummy_secrets.py base/secrets.py
fi
if [[ ! -e .env ]]; then
  cp dummy.env .env
fi

# check for postgres directories
if [[ ! -d pg_data/data ]]; then
  mkdir -p pg_data/data
fi
if [[ ! -d pg_data/logs ]]; then
  mkdir -p pg_data/logs
fi

# check for neo4j directories
if [[ ! -d neo4j/data ]]; then
  mkdir -p neo4j/data
fi
if [[ ! -d neo4j/imports ]]; then
  mkdir -p neo4j/imports
fi
if [[ ! -d neo4j/logs ]]; then
  mkdir -p neo4j/logs
fi

# check for nginx configuration
if [[ ! -e nginx/default.conf ]]; then
  cp nginx/ns_core_nginx_ssl.conf nginx/default.conf
fi

exit 0;