# Additional Libraries and Packages

The contents of this document should describe how to build/run/test the library or package as a single entity outside of the larger Notary Service framework.

Testing should make use of [pytest](https://docs.pytest.org/en/latest/), and be clearly defined within a **testing** section of this document.

## ns_workflow: Workflow Graph Library for Notary Service

Location: [lib/ns_workflow](ns_workflow/)

The code expects a version of Neo4j running. We've provided a docker based implemenation for testing (`docker pull rencinrig/neo4j-apoc:latest`). 

**NOTE**: All commands are assumed to be run from wihtin the `lib/` directory of the repository.

### Setup and configuration

A `ns_workflow_setup.sh` script exists to export the required environment varialbes to test the code

```bash
# Where Neo4J in Docker thinks external files come from
export NEO4J_DOCKER_PATH='/imports/'
# Where the matching host path is
export NEO4J_HOST_PATH=$(pwd)'/neo4j'
# Neo4j Bolt URL
export NEO4J_BOLT_URL='bolt://127.0.0.1:7687'
# Neo4j API User
export NEO4J_USER='neo4j'
# Neo4j API Password
export NEO4J_PASS='password'
```

Source the setup script and start the neo4j docker container

```
source ./ns_workflow_setup.sh
docker run -d \
  --user=$(id -u):$(id -g) \
  --name=neo4j \
  --publish=7473:7473 \
  --publish=7474:7474 \
  --publish=7687:7687 \
  --volume=${NEO4J_HOST_PATH:-$(pwd)/neo4j/data}:/data \
  --volume=${NEO4J_HOST_PATH:-$(pwd)/neo4j/logs}:/logs \
  --volume=${NEO4J_HOST_PATH:-$(pwd)/neo4j}:${NEO4J_DOCKER_PATH:-/imports/} \
  -e NEO4J_AUTH=${NEO4J_USER:-neo4j}/${NEO4J_PASS:-password} \
  rencinrig/neo4j-apoc:latest
```

Validate that the container is running and is ready to use

```console
$ docker logs neo4j
...
2018-12-07 21:29:20.574+0000 INFO  ======== Neo4j 3.5.0 ========
2018-12-07 21:29:20.582+0000 INFO  Starting...
2018-12-07 21:29:28.299+0000 INFO  Bolt enabled on 0.0.0.0:7687.
2018-12-07 21:29:30.127+0000 INFO  Started.
2018-12-07 21:29:31.425+0000 INFO  Remote interface available at http://localhost:7474/
```



Create a python3 virtual environment and install ns_workflow and pytest

```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --editable ns_workflow/
pip install pytest
```

## Testing

The unit tests can be run using `pytest` as follows:

```
pytest -v ns_workflow
```

Example use of pytest (many other runtime options exist):

```console
$ pytest -v ns_workflow
=========================================================== test session starts ============================================================
platform darwin -- Python 3.7.1, pytest-4.0.1, py-1.7.0, pluggy-0.8.0 -- /Users/stealey/GitHub/nrig/notary-service/lib/venv/bin/python3.7
cachedir: .pytest_cache
rootdir: /Users/stealey/GitHub/nrig/notary-service, inifile: pytest.ini
collected 7 items

ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_import_workflow PASSED                                               [ 14%]
ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_import_workflow_auto PASSED                                          [ 28%]
ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_validate PASSED                                                      [ 42%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_adjacent PASSED                                                  [ 57%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_find_node PASSED                                                 [ 71%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_reachable PASSED                                                 [ 85%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_start_node PASSED                                                [100%]

============================================================= warnings summary =============================================================
venv/lib/python3.7/site-packages/networkx/classes/graph.py:23
  /Users/stealey/GitHub/nrig/notary-service/lib/venv/lib/python3.7/site-packages/networkx/classes/graph.py:23: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
    from collections import Mapping

venv/lib/python3.7/site-packages/networkx/classes/reportviews.py:95
  /Users/stealey/GitHub/nrig/notary-service/lib/venv/lib/python3.7/site-packages/networkx/classes/reportviews.py:95: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
    from collections import Mapping, Set, Iterable
  /Users/stealey/GitHub/nrig/notary-service/lib/venv/lib/python3.7/site-packages/networkx/classes/reportviews.py:95: DeprecationWarning: Using or importing the ABCs from 'collections' instead of from 'collections.abc' is deprecated, and in 3.8 it will stop working
    from collections import Mapping, Set, Iterable

-- Docs: https://docs.pytest.org/en/latest/warnings.html
=================================================== 7 passed, 3 warnings in 3.58 seconds ===================================================
```

### Teardown and Cleanup

The environment can be cleaned up by stopping and removing the neo4j docker container, it's mounted volumes, and flushing the virtual environment.

```
docker stop neo4j
docker rm -fv neo4j
rm -rf neo4j/
deactivate
rm -rf venv/
```

