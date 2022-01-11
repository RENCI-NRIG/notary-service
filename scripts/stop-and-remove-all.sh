#!/usr/bin/env bash

# Remove all deployment related components and reset as clean environment

# run from top level of repository
if [[ $(pwd | rev | cut -d '/' -f1 | rev) == 'scripts' ]]; then
  cd ../
fi

# bring down uwsgi services and docker containers
ps -u $(id -u) -o pid,command | grep uwsgi | awk '{print  $  1 }' | grep -E '[0-9]' | xargs kill -9
docker-compose stop
docker-compose rm -f
docker run --rm \
  -v $(pwd):/clean \
  -e UID=$(id -u) \
  -e GID=$(id -g) \
  nginx:1 /bin/bash -c 'chown -R $UID:$GID /clean'
docker volume prune -f
docker network prune -f

# remove runtime directories and __pycache__ directories
rm -rf \
  static \
  media \
  pg_data \
  neo4j \
  kafka \
  safe/imports \
  .venv
while read line; do
  rm -rf $line;
done < <(find . -type d -name __pycache__)

# remove migrations files
while read line; do
  rm -f $line/00*.py;
done < <(find $(pwd) -type d -not -path "*/venv*" -not -path "*/.venv*" -name migrations)

# replace static directory with one from git
git checkout \
  static \
  media

exit 0;