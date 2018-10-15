import unittest
from workflow.graph.neo4j import Neo4jWorkflow
import os

class TestGraphImport(unittest.TestCase):
    NEO4J_HOST_PATH_ENV = 'NEO4J_HOST_PATH'
    NEO4J_DOCKER_PATH_ENV = 'NEO4J_DOCKER_PATH'
    ASSIGNED_ID="NEW-ID"
    TEST_ROLE="PI"

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
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        self.gid = self.neo4j.import_workflow(graphml, self.ASSIGNED_ID)
        self.assertEqual(self.gid, self.ASSIGNED_ID)
        print("\nUsing graph id ", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole=self.TEST_ROLE), 8)

    def test_import_workflow_auto(self):
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        self.gid = self.neo4j.import_workflow(graphml)
        print("\nUsing graph id ", self.gid)
        self.assertEqual(self.neo4j.count_nodes(self.gid), 18)
        self.assertEqual(self.neo4j.count_nodes(self.gid, nodeRole="PI"), 8)

    def tearDown(self):
        if self.gid is not None:
            self.neo4j.delete_workflow(self.gid)

if __name__ == '__main__':
    unittest.main()
