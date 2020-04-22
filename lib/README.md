# Additional Libraries and Packages

The contents of this document should describe how to build/run/test the library or package as a single entity outside of the larger Notary Service framework.

Testing should make use of [pytest](https://docs.pytest.org/en/latest/), and be clearly defined within a **testing** section of this document.

## `ns_workflow`: Workflow Graph Library for Notary Service

Location: [lib/ns_workflow](ns_workflow/)

The code expects a version of Neo4j running. We've provided a docker based implemenation for testing (`docker pull rencinrig/neo4j-apoc:latest`).

**NOTE**: All commands are assumed to be run from wihtin the `lib/` directory of the repository.

### Setup and configuration

A `ns_workflow_setup.sh` script exists to export the required environment varialbes to test the code

```bash
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
  --volume=$(pwd)/neo4j/data:/data \
  --volume=${NEO4J_IMPORTS_PATH_HOST:-$(pwd)/neo4j/imports}:${NEO4J_IMPORTS_PATH_DOCKER:-/imports} \
  --volume=$(pwd)/neo4j/logs:/logs \
  -e NEO4J_AUTH=${NEO4J_USER:-neo4j}/${NEO4J_PASS:-password} \
  rencinrig/neo4j-apoc:latest
```

Validate that the container is running and is ready to use

```console
$ docker logs neo4j
...
2019-01-03 20:02:35.639+0000 INFO  ======== Neo4j 3.5.0 ========
2019-01-03 20:02:35.659+0000 INFO  Starting...
2019-01-03 20:02:51.234+0000 INFO  Bolt enabled on 0.0.0.0:7687.
2019-01-03 20:02:55.262+0000 INFO  Started.
2019-01-03 20:02:57.626+0000 INFO  Remote interface available at http://localhost:7474/
```

Create a python3 virtual environment and install ns_workflow and pytest

```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --editable ns_workflow/
pip install pytest
```

For performance reasons it is critical to create Neo4j indexes as follows (using the console or by scripting):
```
CREATE INDEX ON :Node(GraphID)
CREATE INDEX ON :Node(GraphID, ID)
CREATE INDEX ON :Node(GraphID, Type)
CREATE INDEX ON :Node(GraphID, ID, Type)
```

Available indexes can be checked via console by using the `:schema` comand.

### Testing

The unit tests can be run using `pytest` as follows:

```
pytest -v ns_workflow
```

Example use of pytest (many other runtime options exist):

```console
$ pytest -v ns_workflow
=========================================================== test session starts ============================================================
platform darwin -- Python 3.7.1, pytest-4.0.2, py-1.7.0, pluggy-0.8.0 -- /Users/stealey/GitHub/nrig/notary-service/lib/venv/bin/python3.7
cachedir: .pytest_cache
rootdir: /Users/stealey/GitHub/nrig/notary-service/lib, inifile: pytest.ini
collected 7 items

ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_import_workflow PASSED                                               [ 14%]
ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_import_workflow_auto PASSED                                          [ 28%]
ns_workflow/tests/graphml_import_test.py::TestGraphImport::test_validate PASSED                                                      [ 42%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_adjacent PASSED                                                  [ 57%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_find_node PASSED                                                 [ 71%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_reachable PASSED                                                 [ 85%]
ns_workflow/tests/graphml_query_test.py::TestGraphQuery::test_query_start_node PASSED                                                [100%]

========================================================= 7 passed in 4.96 seconds =========================================================
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

## `ns_jwt`: JSON Web Tokens for Notary Service

We will use RS256 (public/private key) variant of JWT signing. (Source: https://pyjwt.readthedocs.io/en/latest/usage.html#encoding-decoding-tokens-with-rs256-rsa). For signing, , NS is assumed to be in possession of a public-private keypair. Presidio can access the public key through static configuration or, possibly, by querying an endpoint on NS, that is specified in the token.

NS tokens carry the following claims:

| name | description | type |
| --- | --- | --- |
|data-set | SAFE token pointing to the dataset being accessed (generated by the data provider/owner and passed on to NS at the time of dataset registration) | String, Private |
| project-id | CoManage/NS name of the project, universally unique and distinct. | String, Private |
| ns-token | SAFE Token of the NS generated from its public key | String, Private |
| ns-name | Human-readable NS name | String, Private |
| iss | NS FQDN | String, Registered |
| sub | OSF DCE rendering of DN attributes from user’s X.509 cert | String, Public |
| exp | Expiration date | Date, Registered |
| iat | Issued at date | Date, Registered |
| name | Full name of subject | String, Public |
| ver | Version of the encoding | Private |

For dates, a JSON numeric value representing the number of seconds from 1970-01-01T00:00:00Z UTC until the specified UTC date/time, ignoring leap seconds.  This is equivalent to the IEEE Std 1003.1, 2013 Edition definition "Seconds Since the Epoch", in which each day is accounted for by exactly 86400 seconds, other than that non-integer values can be represented.  See RFC 3339 for details regarding date/times in general and UTC in particular.

### Setup and configuration

No external configuration except for dependencies (PyJWT, cryptography, python-dateutil).

As above, use a virtual environment
```
virtualenv -p $(which python3) venv
source venv/bin/activate
pip install --editable ns_jwt
pip install pytest
```

### Testing

Simply execute the command below. The test relies on having `public.pem` and `private.pem` (public and private portions of an RSA key) to be present in the `tests/` directory. You can generate new pairs using `tests/gen-keypair.sh` (relies on openssl installation).

```
pytest -v ns_jwt
```

### Teardown and Cleanup

None needed.

### Troubleshooting

CI Logon or other JWTs may not decode outright using PyJWT due to `binascii.Error: Incorrect padding` and `jwt.exceptions.DecodeError: Invalid crypto padding`. This is due to lack of base64 padding at the end of the token. Read it in as a string, then add the padding prior to decoding:

```
import jwt

with open('token_file.jwt') as f:
  token_string = f.read()

jwt.decode(token_string + "==", verify=False)
```
Any number of `=` can be added (at least 2) to fix the padding. If token is read in as a byte string, convert to `utf-8` first: `jwt_str = str(jwt_bin, 'utf-8')`, then add padding (Source: https://gist.github.com/perrygeo/ee7c65bb1541ff6ac770)
