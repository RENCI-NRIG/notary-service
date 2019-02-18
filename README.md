# Notary Service

### Status

[![Requirements Status](https://requires.io/github/RENCI-NRIG/notary-service/requirements.svg?branch=master)](https://requires.io/github/RENCI-NRIG/notary-service/requirements/?branch=master)

**What is the Notary Service?** - TODO

**Requirements**: There are a small set of system requirements in order to run this code. If you're planning on doing additional development to this codebase, then additional requirements may be applicable.

- To Run
  - Docker
  - Docker Compose

- To Develop
  - Docker
  - Docker Compose
  - Python 3 / Pip 3
  - Virtualenv

## Table of Contents

- [TL;DR](#tldr) - Just run it all in Docker and I don't care about specifics
- [Scripts](#scripts) - Convenience scripts for setting up or tearing down a development environment
- [Environment and Configuration](#env) - How to setup your development environment
- [Virtualenv](#venv) - Establish a Python virtual environment
- [Build](#build) - Building the stack
- [Run](#run) - Running the stack
- [Docker](#docker) - I want to do all of this in docker
- [Lib](#libs) - Additional libraries/packages for Notary Service
- [References](#ref) - Reference information about all the things

## <a name="tldr"></a>TL;DR

**NOTE**: Assumes you already have OIDC Client credentials, and LDAP access setup for a COmanage Registry.

```
cp env.template .env                                  # set variables accordingly
cp base/env.template base/.env                        # set variables accordingly
cp base/secrets.py.template base/secrets.py           # set variables accordingly
cp nginx/default.conf.template nginx/default.conf     # configure accordingly
source base/.env
UWSGI_UID=$(id -u) UWSGI_GID=$(id -g) docker-compose up -d
```

Once all of the containers have completed their startup scripts, you will find the running notary service at the specified URL.

Example: [https://127.0.0.1:8443/](https://127.0.0.1:8443/)

<img width="80%" alt="Landing page" src="https://user-images.githubusercontent.com/5332509/50703546-7cc92400-1022-11e9-9004-924d8ed9713e.png">

Wait! What if I don't know how to **set variables accordingly** or to **configure accordingly**?.. Then keep reading below.

## <a name="scripts"></a>Scripts

Convenience scripts are provided in the `scripts` directory. The scripts are somewhat macOS specific due the primary development environment, but can be modified to run elsewhere.

1. [macos-development-environment.sh](scripts/macos-development-environment.sh) - generates the directories and environment stubs for the user to populate with their own configuration parameters, and starts the **database**, **neo4j**, and **nginx** containers.

2. [stop-and-remove-all.sh](scripts/stop-and-remove-all.sh) - as the name suggests, stops all running containers, removes them, and purges the system of user created container volume mounts.

Move on to the [Environment and Configuration](#env) section.

## <a name="env"></a>Environment and Configuration

Your project must be configured prior to running it for the first time. Example configuration files have been provided as templates to start from.

Do not check any of your configuration files into a repository as they will contain your projects **secrets** (use `.gitignore` to exclude any files containing secrets).

1. **.env** from [env.template](env.template) - Environment variables for docker-compose.yml to use
2. **base/.env** from [base/env.template](base/env.template) - Environment variables for Django to use via the dotenv package
3. **base/secrets.py** from [base/secrets.py.template](base/secrets.py.template) - Django requires a secret key and this file provides an example.
4. **nginx/default.conf** from [nginx/default.conf.template](nginx/default.conf.template) - Example Nginx SSL configuration file to use for deployment.

### `.env`

A file named `env.template` has been provided as an example, and is used by the `docker-compose.yml` file.

```
cp env.template .env
```

Once copied, modify the default values for each to correspond to your desired deployment. The UID and GID based entries should correspond to the values of the user responsible for running the code as these will relate to shared volumes from the host to the running containers.

```env
# docker-compose environment file
#
# When you set the same environment variable in multiple files,
# here’s the priority used by Compose to choose which value to use:
#
#  1. Compose file
#  2. Shell environment variables
#  3. Environment file
#  4. Dockerfile
#  5. Variable is not defined

# database PostgreSQL - default values should not be used in production
POSTGRES_PASSWORD=postgres
POSTGRES_USER=postgres
PGDATA=/var/lib/postgresql/data
POSTGRES_DB=postgres
POSTGRES_PORT=5432

# django
UWSGI_UID=1000
UWSGI_GID=1000

# nginx
NGINX_DEFAULT_CONF=./nginx/default.conf
NGINX_SSL_CERT=./ssl/ssl_dev.crt
NGINX_SSL_KEY=./ssl/ssl_dev.key

# neo4J
NEO4J_UID=1000
NEO4J_GID=1000
NEO4J_DATA_PATH_HOST=./neo4j/data
NEO4J_DATA_PATH_DOCKER=/data
NEO4J_IMPORTS_PATH_HOST=./neo4j/imports
NEO4J_IMPORTS_PATH_DOCKER=/imports
NEO4J_LOGS_PATH_HOST=./neo4j/logs
NEO4J_LOGS_PATH_DOCKER=/logs
NEO4J_BOLT_URL=bolt://127.0.0.1:7687
NEO4J_USER=neo4j
NEO4J_PASS=password
NEO4J_HOST=127.0.0.1
```

### `base/.env`

A file named `base/dummy.env` has been provided as an example, and is used by Django's python-dotenv package.

If you're planning on doing local development with virutalenv, configure the database to be reachable from the local machine.

- Update `POSTGRES_HOST` in `.env` to reflect the IP of your local machine (For example, from `export POSTGRES_HOST=database` to  `export POSTGRES_HOST=127.0.0.1`)

```
cp base/env.template base/.env
```

Once copied, update the variables to correspond with your deployment needs. The OIDC_RP_CLIENT values should come from your OIDC COmanage registry and the LDAP values would be provided by CILogon personnel. Default host information relates to localhost (127.0.0.1) and should be adjusted according to the hostname or IP your running on.

```env
# Settings for environment. Notes:
#
#  - Since these are bash-like settings, there should be no space between the
#    variable name and the value (ie, "A=B", not "A = B")
#  - Boolean values should be all lowercase (ie, "A=false", not "A=False")

# debug - set to false in production
export DEBUG=true

# uwsgi user
export UWSGI_UID=$(id -u)
export UWSGI_GID=$(id -g)

# database PostgreSQL - default values should not be used in production
export POSTGRES_PASSWORD=postgres
export POSTGRES_USER=postgres
export PGDATA=/var/lib/postgresql/data
export POSTGRES_DB=postgres
export POSTGRES_HOST=database
export POSTGRES_PORT=5432

# CILogon / COmanage - values provided when OIDC client is created
export OIDC_RP_CLIENT_ID=''
export OIDC_RP_CLIENT_SECRET=''

# LDAP - values provided by CILogon staff
export LDAP_HOST=''
export LDAP_USER=''
export LDAP_PASSWORD=''
export LDAP_SEARCH_BASE=''

# Neo4j
export NEO4J_UID=$(id -u)
export NEO4J_GID=$(id -g)
export NEO4J_DATA_PATH_HOST=./neo4j/data
export NEO4J_DATA_PATH_DOCKER=/data
export NEO4J_IMPORTS_PATH_HOST=./neo4j/imports
export NEO4J_IMPORTS_PATH_DOCKER=/imports
export NEO4J_LOGS_PATH_HOST=./neo4j/logs
export NEO4J_LOGS_PATH_DOCKER=/logs
export NEO4J_BOLT_URL=bolt://127.0.0.1:7687
export NEO4J_USER=neo4j
export NEO4J_PASS=password
export NEO4J_HOST=127.0.0.1
```

### `base/secrets.py`

A file named `base/secrets.py.template` has been provided as an exmaple.

Generate a `SECRET_KEY` and save in in this file

```
cp base/secrets.py.template base/secrets.py
```

Once copied, uncomment the SECRET_KEY line and add a key (example below)

```python
# Secret Key
# You must uncomment, and set SECRET_KEY to a secure random value
# e.g. https://djskgen.herokuapp.com/

SECRET_KEY = '1123*n%5ep$n2cmd9ul*qgr+uzc!d*47h$u_tdhk+x0_v+%z5a'
```

### `nginx/default.conf`

A file named `nginx/default.conf.template` has been provided as an exmaple.

```
cp nginx/default.conf.template nginx/default.conf
```

Once copied, entries for `FQDN_OR_IP` should be replaced with actual hostnames or IPs along with port information if not using default values. Also note that macOS will not use file based sockets, so TCP sockets should be used instead.

```nginx
# the upstream component nginx needs to connect to
upstream django {
    server unix:///code/base.sock; # UNIX file socket
    # Defaulting to macOS equivalent of docker0 network for TCP socket
    #server host.docker.internal:8000; # TCP socket
}

server {
    listen 80;
    server_name FQDN_OR_IP;
    return 301 https://FQDN_OR_IP$request_uri;
}

server {
    listen   443 ssl default_server;
    # the domain name it will serve for
    server_name FQDN_OR_IP; # substitute your machine's IP address or FQDN

    # If they come here using HTTP, bounce them to the correct scheme
    error_page 497 https://$server_name$request_uri;
    # Or if you're on the default port 443, then this should work too
    # error_page 497 https://;

    ssl_certificate /etc/ssl/SSL.crt;
    ssl_certificate_key /etc/ssl/SSL.key;

    charset     utf-8;

    # max upload size
    client_max_body_size 75M;   # adjust to taste

    # Django media
    location /media  {
        alias /code/media;  # your Django project's media files - amend as required
    }

    location /static {
        alias /code/static; # your Django project's static files - amend as required
    }

    # Finally, send all non-media requests to the Django server.
    location / {
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Host $http_host;
        proxy_redirect off;

        uwsgi_pass  django;
        include     /code/uwsgi_params; # the uwsgi_params file
    }
}
```
- **NOTE**: `host.docker.internal` is macOS specific, substitute as required by your operating system

### `docker-compose.yml`

Double check that all variable references found in `.env`, or their default values are suitable for your deployment.

If you're planning on doing local development with virutalenv, configure the database to be reachable from the local machine.

- Ensure the `POSTGRES_PORT=5432` is properly mapped to the host in the `docker-compose.yml` file

### `ns_core_uwsgi.ini`

**NOTE**: Depending on your system (macOS) you may not be able to run the Nginx server using sockets mounted from the host. For more information refer to this Github issue: [Support for sharing unix sockets](https://github.com/docker/for-mac/issues/483). If this is the case, you'll either need to run your Nginx server over ports, or run everything in Docker. The following will describe how to run the Nginx server using TCP ports.

Update the uWSGI ini file

```ini
...
; use protocol uwsgi over TCP socket (use if UNIX file socket is not an option)
socket              = :8000
; add an http router/server on the specified address **port**
;http                = :8000
; map mountpoint to static directory (or file) **port**
;static-map          = /static/=static/
;static-map          = /media/=media/
; bind to the specified UNIX/TCP socket using uwsgi protocol (full path) **socket**
;uwsgi-socket        = ./example.sock
; ... with appropriate permissions - may be needed **socket**
;chmod-socket        = 666
...
```
Move on to the [Virtualenv](#venv) section.

## <a name="venv"></a>Virtualenv

By default this project is configured to run everything in Docker which may be non-optimal for development. In order to enable local development using Python 3 the user must make a few small changes prior to running the code.

If you're only wanting to run this in Docker, move on to the [Docker](#docker) section.

### Using virtualenv locally

Create the virtual environment and install packages

```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Move on to the [Build](#build) section.

## <a name="build"></a>Build

Once all configuration has been done, the user can build the necessary containers by issuing:

```
docker-compose build
```

Anytime a modification is made to the Django code, a new container should be built prior to launching the docker-compose definition.

Move on to the [Run](#run) section.

## <a name="run"></a>Run

Be sure to source the environment variables that were configured from the `/base/.env` file.

```
source base/.env
```

### database

Create the database directories if they do not exist

```
mkdir -p pg_data/data pg_data/logs
```

Start the pre-defined PostgreSQL database in Docker

```
docker-compose up -d database
```

Validate that the database container is running.

```console
$ docker-compose ps
  Name                Command              State           Ports
-------------------------------------------------------------------------
database   docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
```

### neo4j

Create the neo4j directories if they do not exist

```
mkdir -p neo4j/data neo4j/imports neo4j/logs
```

Start the pre-defined PostgreSQL database in Docker

```
docker-compose up -d neo4j
```

Validate that the neo4j container is running.

```console
$ docker-compose ps
  Name                Command              State           Ports
-------------------------------------------------------------------------
database   docker-entrypoint.sh postgres   Up      0.0.0.0:5432->5432/tcp
```

### django

Start the Django service

- Local virtualenv
  - Launch the `run_uwsgi.sh` script from your virtualenv, passing in your UID and GID values

  ```
  UWSGI_UID=$(id -u) UWSGI_GID=$(id -g) ./run_uwsgi.sh
  ```
  **NOTE**: The process output should remain observable in the terminal after running this command, use `ctrl-c` to end the process, or `ctrl-z` to suspend it.

- Docker only
  - Launch `django` container from docker-compose

  ```
  docker-compose up -d django
  ```
  Validate that the service is running
  
    ```console
    $ docker-compose ps
      Name                Command              State                      Ports
    ----------------------------------------------------------------------------------------------
    ...
    django     /code/docker-entrypoint.sh      Up      0.0.0.0:8000->8000/tcp
    ...
    ```

### nginx

Start the nginx service

```
$ docker-compose up -d nginx
```

Validate that the service is running on the expected port(s)

```console
$ docker-compose ps
  Name                Command              State                      Ports
----------------------------------------------------------------------------------------------
...
nginx      nginx -g daemon off;            Up      0.0.0.0:8443->443/tcp, 0.0.0.0:8080->80/tcp
...
```

At this point the notary-service stack should be running and can be verified at your defined URL: [http(s)://HOSTNAME:PORT](http://127.0.0.1:8080)

## <a name="docker"></a>Docker

TODO

## <a name="lib"></a>Lib

TODO

### ns_workflow

Neo4j/APOC graph database for managing Notary Service Workflows. Build information at [https://github.com/RENCI-NRIG/impact-docker-images/tree/master/neo4j](https://github.com/RENCI-NRIG/impact-docker-images/tree/master/neo4j)


## <a name="ref"></a>References

### Django / Python / Nginx

- Django docs: [https://docs.djangoproject.com/en/2.0/](https://docs.djangoproject.com/en/2.0/)
- uWSGI options: [http://uwsgi-docs.readthedocs.io/en/latest/Options.html](http://uwsgi-docs.readthedocs.io/en/latest/Options.html)
- Nginx docs: [https://nginx.org/en/docs/](https://nginx.org/en/docs/)

### Docker

- Docker docs: [https://docs.docker.com](https://docs.docker.com)
- Docker Compose docs: [https://docs.docker.com/compose/](https://docs.docker.com/compose/)
