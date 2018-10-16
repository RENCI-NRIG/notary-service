import unittest
from workflow.graph.neo4j import Neo4jWorkflow
from workflow.graph.abstract_workflow import WorkflowException
import os
import logging


class SingletonTestInitializer:
    """ initialize neo4j logging but only once, no matter how many tests are run """
    class __SingletonTestInitializer:
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

    instance = None

    def __init__(self):
        if SingletonTestInitializer.instance is None:
            SingletonTestInitializer.instance = SingletonTestInitializer.__SingletonTestInitializer()

    def logger(self):
        return SingletonTestInitializer.instance.log


class TestGraphImport(unittest.TestCase):
    NEO4J_HOST_PATH_ENV = 'NEO4J_HOST_PATH'
    NEO4J_DOCKER_PATH_ENV = 'NEO4J_DOCKER_PATH'
    ASSIGNED_ID="NEW-ID"
    TEST_ROLE="PI"

    def __init__(self, *args, **kwargs):
        super(TestGraphImport, self).__init__(*args, **kwargs)

        sti = SingletonTestInitializer()

        # configure my log
        self.log = sti.logger()

    def setUp(self):
        if self.NEO4J_HOST_PATH_ENV not in os.environ.keys() or \
                self.NEO4J_DOCKER_PATH_ENV not in os.environ.keys():
            raise Exception(' '.join(['Environment variables', self.NEO4J_HOST_PATH_ENV,
                            'and', self.NEO4J_DOCKER_PATH_ENV, 'must be specified']))
        self.neo4j = Neo4jWorkflow("bolt://localhost:7687", "neo4j", "admin",
                              importHostDir=os.environ[self.NEO4J_HOST_PATH_ENV],
                              importDir=os.environ[self.NEO4J_DOCKER_PATH_ENV])
        self.gid = None


    def test_import_workflow(self):
        self.log.info("Importing graph with assigned ID")
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml, self.ASSIGNED_ID)
        except WorkflowException as wexc:
            self.log.error(wexc)
            self.assertTrue(False)
        self.assertEqual(self.gid, self.ASSIGNED_ID)
        self.log.info("Using graph id %s", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole=self.TEST_ROLE), 8)

    def test_import_workflow_auto(self):
        self.log.info("Importing graph with self-generated ID")
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml)
        except WorkflowException as wexc:
            self.log.error(wexc)
            self.assertTrue(False)
        self.log.info("Using graph id %s", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole="PI"), 8)

    def test_validate(self):
        self.log.info("Testing graph validation")
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml)
            self.log.info("Using graph id %s", self.gid)
            self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
            self.neo4j.validate_workflow(self.gid)
        except WorkflowException as wexc:
            self.log.error(wexc)
            self.assertTrue(False)

    def tearDown(self):
        if self.gid is not None:
            self.neo4j.delete_workflow(self.gid)

if __name__ == '__main__':
    unittest.main()
