# Workflow Graph Library for Notary Service

## Running the unit tests

The code expects a (potentially) dockerized version of Neo4j running. There is a Bash script that sets up two environment variables: 
```
# Where Neo4J in Docker thinks external files come from 
export NEO4J_DOCKER_PATH=/imports/
# Where the matching host path is
export NEO4J_HOST_PATH=/wherever/files/on/the/host/reside
```

It must be sourced prior to running the unit tests. The unit tests can be executed as follows:

```
python -m workflow.tests.graphml_import_test 
```

from the lib/ directory

