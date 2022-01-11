# Docker Compose

Example docker compose service files are provided as a starting point depending on the type of deployment being used.

## Development

Expose all communication ports used by the containers for debugging purposes.

### `local-development.yml` (default)

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


## Production

Only expose http and https ports for the Nginx container.

### `production-compose.yml`

Ports exposed throught the host are as follows:

Nginx:

- http: `80`
- https: `443`

### `selinux-compose.yml`

Ports exposed throught the host are as follows:

Nginx:

- http: `80`
- https: `443`


**NOTE**: Volume mounts must include the `:z` option and the SSL key file requires `+r` rights for the neo4j container to use it.
