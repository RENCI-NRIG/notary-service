FROM python:3.7
MAINTAINER Michael J. Stealey <mjstealey@gmail.com>

RUN apt-get update && apt-get install -y \
  postgresql-client \
  && pip install virtualenv \
  && mkdir /code/

WORKDIR /code
VOLUME ["/code"]
ENTRYPOINT ["/code/docker-entrypoint.sh"]
