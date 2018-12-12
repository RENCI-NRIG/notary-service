# Notary Service

### Status

[![Requirements Status](https://requires.io/github/RENCI-NRIG/notary-service/requirements.svg?branch=master)](https://requires.io/github/RENCI-NRIG/notary-service/requirements/?branch=master)
[![Coverage Status](https://coveralls.io/repos/github/RENCI-NRIG/notary-service/badge.svg?branch=master)](https://coveralls.io/github/RENCI-NRIG/notary-service?branch=master)

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

- [TL;DR](#tldr) - Just run it, I don't care about specifics
- [Environment](#env) - How to setup your development environment
- [Configure](#configure) - Configuration / Settings / Prerequisites
- [Build](#build) - Building the stack
- [Run](#run) - Running the stack
- [Docker](#docker) - I want to do all of this in docker
- [Lib](#libs) - Additional libraries/packages for Notary Service
- [References](#ref) - Reference information about all the things

## <a name="tldr"></a>TL;DR

TODO

## <a name="env"></a>Environment

By default this project is configured to run everything in Docker which may be non-optimal for develoment. In order to enble local development using Python 3 the user must make a few small changes prior to running the code.

If you're only wanting to run this in Docker, move on to the [Docker](#docker) section.

### Using virtualenv locally

Create the virtual environment and install packages

```
$ virtualenv -p $(which python3) venv
$ source venv/bin/activate
(venv)$ pip install --upgrade pip
(venv)$ pip install -r requirements.txt
```

Move on to the [Configure](#configure) section.

## <a name="configure"></a>Configure

Your project must be configured prior to running it for the first time. Example configuration files have been provided as templates to start from.

Do not check any of your configuration files into a repository as they will contain your projects **secrets** (use `.gitignore` to exclude any files containing secrets).

### `base/secrets.py`

A file named `dummy_secrets.py` has been provided as an exmaple.

```console
$ cp dummy_secrets.py secrets.py
```

Generate a `SECRET_KEY` and save in in this file

### `base/.env`

A file named `dummy.env` has been provided as an exmaple.

```console
$ cp dummy.env .env
```

Modify the environment varialbes in the `.env` file to coincide with the settings you'll be using in your deployment.

If you're planning on doing local development with virutalenv, configure the database to be reachable from the local machine.

- Update `POSTGRES_HOST` in `.env` to reflect the IP of your local machine (For example, from `export POSTGRES_HOST=database` to  `export POSTGRES_HOST=127.0.0.1`)

### `docker-compose.yml`

If you're planning on doing local development with virutalenv, configure the database to be reachable from the local machine.

- Ensure the `POSTGRES_PORT=5432` is properly mapped to the host in the `docker-compose.yml` file

If using https wiht SSL certificates, update the nginx stanza

```yaml
  nginx:
    image: nginx:latest
    container_name: nginx
    ports:
      - 8080:80
      - 8443:443
    volumes:
      - .:/code
      - ./static:/code/static
      - ./media:/code/media
      - ./nginx/default.conf:/etc/nginx/conf.d/default.conf # SSL configuration file
      - PATH_TO/SSL.crt:/etc/ssl/SSL.crt                    # SSL cert file on host
      - PATH_TO/SSL.key:/etc/ssl/SSL.key                    # SSL key file on host
```

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

### `nginx/default.conf`

Example nginx configurations are provided for http or https, copy the one that is relevant to your deployment scheme.

```console
### for http ###
$ cp nginx/ns_core_nginx.conf nginx/default.conf
### for https ###
$ cp nginx/ns_core_nginx_ssl.conf nginx/default.conf
```

Update the nginx configuration file (http or https)

```conf
upstream django {
    #server unix:///code/${PROJECT_NAME}.sock; # UNIX file socket
    # Defaulting to macOS equivalent of docker0 network for TCP socket
    server host.docker.internal:8000; # TCP socket
}
```

- **NOTE**: `host.docker.internal` is macOS specific, substitute as required by your operating system

Move on to the [Build](#build) section.

## <a name="build"></a>Build

Once all configuration has been done, the user can build the necessary containers by issueing:

```console
$ docker-compose build
```

Anytime a modification is made to the Django code, a new container should be built prior to launching the docker-compose definition.

Move on to the [Run](#run) section.

## <a name="run"></a>Run

Be sure to source the environment variables that were configured from the `/base/.env` file.

```
source base/.env
```

### database

Start the pre-defined PostgreSQL database in Docker

```
$ docker-compose up -d database
```

Validate that the database container is running.

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

  ```console
  $ UWSGI_UID=$(id -u) UWSGI_GID=$(id -g) ./run_uwsgi.sh
  ```
  **NOTE**: The process output should remain observable in the terminal after running this command, use `ctrl-c` to end the process, or `ctrl-z` to suspend it.

- Docker only
  - Launch `django` container from docker-compose

  ```console
  $ docker-compose up -d django
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

Neo4j/APOC graph database for managing Notary Service Workflows


## <a name="ref"></a>References

### Django / Python / Nginx

- Django docs: [https://docs.djangoproject.com/en/2.0/](https://docs.djangoproject.com/en/2.0/)
- uWSGI options: [http://uwsgi-docs.readthedocs.io/en/latest/Options.html](http://uwsgi-docs.readthedocs.io/en/latest/Options.html)
- Nginx docs: [https://nginx.org/en/docs/](https://nginx.org/en/docs/)

### Docker

- Docker docs: [https://docs.docker.com](https://docs.docker.com)
- Docker Compose docs: [https://docs.docker.com/compose/](https://docs.docker.com/compose/)
