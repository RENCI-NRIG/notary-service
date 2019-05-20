# Docker Compose

Example docker compose service files are provided as a starting point depending on the type of deployment being used.

## Development

Expose all communication ports used by the containers for debugging purposes.

### `development-compose.yml` (default)

The default `docker-compose.yml` file is copied from this. Ports exposed throught the host are as follows:

Nginx:

- http: `8080`
- https: `8443`

Postgres:

- port: `5432`

Neo4j:

- http: `7474`
- https: `7473`
- bolt: `7687`

Zookeeper:

- port: `2181`

Kafka:

- port: `9092`

```console
$ docker-compose ps
  Name                 Command               State                                   Ports
---------------------------------------------------------------------------------------------------------------------------
database    docker-entrypoint.sh postgres    Up      0.0.0.0:5432->5432/tcp
django      /code/docker-entrypoint.sh       Up      0.0.0.0:8000->8000/tcp
kafka       start-kafka.sh                   Up      0.0.0.0:9092->9092/tcp
neo4j       /sbin/tini -g -- /docker-e ...   Up      0.0.0.0:7473->7473/tcp, 0.0.0.0:7474->7474/tcp, 0.0.0.0:7687->7687/tcp
nginx       nginx -g daemon off;             Up      0.0.0.0:8443->443/tcp, 0.0.0.0:8080->80/tcp
zookeeper   /bin/sh -c /usr/sbin/sshd  ...   Up      0.0.0.0:2181->2181/tcp, 22/tcp, 2888/tcp, 3888/tcp
```

## Production

Only expose http and https ports for the Nginx container.

### `production-compose.yml`

Ports exposed throught the host are as follows:

Nginx:

- http: `8080`
- https: `8443`

```console
$ docker-compose ps
  Name                 Command               State                      Ports
------------------------------------------------------------------------------------------------
database    docker-entrypoint.sh postgres    Up      5432/tcp
django      /code/docker-entrypoint.sh       Up
kafka       start-kafka.sh                   Up
neo4j       /sbin/tini -g -- /docker-e ...   Up      7473/tcp, 7474/tcp, 7687/tcp
nginx       nginx -g daemon off;             Up      0.0.0.0:8443->443/tcp, 0.0.0.0:8080->80/tcp
zookeeper   /bin/sh -c /usr/sbin/sshd  ...   Up      2181/tcp, 22/tcp, 2888/tcp, 3888/tcp
```

### `selinux-compose.yml`

Ports exposed throught the host are as follows:

Nginx:

- http: `8080`
- https: `8443`

```console
$ docker-compose ps
  Name                 Command               State                    Ports
---------------------------------------------------------------------------------------------
database    docker-entrypoint.sh postgres    Up      5432/tcp
django      /code/docker-entrypoint.sh       Up
kafka       start-kafka.sh                   Up
neo4j       /sbin/tini -g -- /docker-e ...   Up      7473/tcp, 7474/tcp, 7687/tcp
nginx       nginx -g daemon off;             Up      0.0.0.0:8443->443/tcp, 0.0.0.0:8080->80/tcp
zookeeper   /bin/sh -c /usr/sbin/sshd  ...   Up      2181/tcp, 22/tcp, 2888/tcp, 3888/tcp
```

**NOTE**: Volume mounts must include the `:z` option and the SSL key file requires `+r` rights for the neo4j container to use it.
