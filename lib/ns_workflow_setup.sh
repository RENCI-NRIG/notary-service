#!/bin/bash

# Where Neo4J in Docker thinks external files come from
export NEO4J_IMPORTS_PATH_DOCKER='/imports'
# Where the matching host path is
export NEO4J_IMPORTS_PATH_HOST=$(pwd)'/neo4j/imports'
# Neo4j Bolt URL
export NEO4J_BOLT_URL='bolt://127.0.0.1:7687'
# Neo4j API User
export NEO4J_USER='neo4j'
# Neo4j API Password
export NEO4J_PASS='password'