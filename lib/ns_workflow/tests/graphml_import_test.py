import unittest
from ns_workflow import Neo4jWorkflow, WorkflowError
import os
import logging


class TestLogInitializer:
    """ initialize neo4j and unit test logging """
    # Tell pytest to ignore
    __test__=False

    def __init__(self):
        # configure neo4j workflow log
        neo4jlog = logging.getLogger('workflow.graph.neo4j')
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(name)s %(asctime)s %(message)s'))
        neo4jlog.addHandler(ch)
        neo4jlog.setLevel(logging.DEBUG)

        self.log = logging.getLogger('workflow.graph.unittest')
        ch = logging.StreamHandler()
        ch.setFormatter(logging.Formatter('%(name)s %(asctime)s %(message)s'))
        self.log.addHandler(ch)
        self.log.setLevel(logging.INFO)

    def logger(self):
        return self.log


global loginit, testdir
testdir = os.path.dirname(os.path.dirname(__file__)) + '/tests/'


class TestGraphImport(unittest.TestCase):
    NEO4J_IMPORTS_PATH_HOST_ENV = 'NEO4J_IMPORTS_PATH_HOST'
    NEO4J_IMPORTS_PATH_DOCKER_ENV = 'NEO4J_IMPORTS_PATH_DOCKER'
    NEO4J_BOLT_URL_ENV = 'NEO4J_BOLT_URL'
    NEO4J_USER_ENV = 'NEO4J_USER'
    NEO4J_PASS_ENV = 'NEO4J_PASS'

    TEST_ASSIGNED_ID = "NEW-ID"
    TEST_ROLE = "PI"

    def __init__(self, *args, **kwargs):
        super(TestGraphImport, self).__init__(*args, **kwargs)

        # sti = SingletonTestInitializer()

        # configure my log
        # self.log = sti.logger()
        loginit = logging
        self.log = loginit.getLogger(__name__)

    def setUp(self):
        if self.NEO4J_IMPORTS_PATH_HOST_ENV not in os.environ.keys() or \
                self.NEO4J_IMPORTS_PATH_DOCKER_ENV not in os.environ.keys() or \
                self.NEO4J_BOLT_URL_ENV not in os.environ.keys() or \
                self.NEO4J_USER_ENV not in os.environ.keys() or \
                self.NEO4J_PASS_ENV not in os.environ.keys():
            raise Exception(' '.join(['Environment variables', self.NEO4J_IMPORTS_PATH_HOST_ENV, 'and',
                                      self.NEO4J_IMPORTS_PATH_DOCKER_ENV, 'and',
                                      self.NEO4J_BOLT_URL_ENV, 'and',
                                      self.NEO4J_USER_ENV, 'and',
                                      self.NEO4J_PASS_ENV, 'must be specified']))
        self.neo4j = Neo4jWorkflow(os.environ[self.NEO4J_BOLT_URL_ENV],
                                   os.environ[self.NEO4J_USER_ENV],
                                   os.environ[self.NEO4J_PASS_ENV],
                                   importHostDir=os.environ[self.NEO4J_IMPORTS_PATH_HOST_ENV],
                                   importDir=os.environ[self.NEO4J_IMPORTS_PATH_DOCKER_ENV])
        self.gid = None

    def test_import_workflow(self):
        self.log.info("Importing graph with assigned ID")
        graphmlFile = open(testdir + "test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml, self.TEST_ASSIGNED_ID)
        except WorkflowError as wexc:
            self.log.error(wexc)
            self.assertTrue(False)
        self.assertEqual(self.gid, self.TEST_ASSIGNED_ID)
        self.log.info("Using graph id %s", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole=self.TEST_ROLE), 8)

    def test_import_workflow_auto(self):
        self.log.info("Importing graph with self-generated ID")
        graphmlFile = open(testdir + "test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml)
        except WorkflowError as wexc:
            self.log.error(wexc)
            self.assertTrue(False)
        self.log.info("Using graph id %s", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole="PI"), 8)

    def test_validate(self):
        self.log.info("Testing graph validation")
        graphmlFile = open(testdir + "test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml)
            self.log.info("Using graph id %s", self.gid)
            self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
            self.neo4j.validate_workflow(self.gid)
        except WorkflowError as wexc:
            self.log.error(wexc)
            self.assertTrue(False)

    def tearDown(self):
        if self.gid is not None:
            self.neo4j.delete_workflow(self.gid)


if __name__ == '__main__':
    loginit = TestLogInitializer()
    unittest.main()
