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


class TestGraphQuery(unittest.TestCase):
    NEO4J_HOST_PATH_ENV = 'NEO4J_HOST_PATH'
    NEO4J_DOCKER_PATH_ENV = 'NEO4J_DOCKER_PATH'
    NEO4J_BOLT_URL_ENV = 'NEO4J_BOLT_URL'
    NEO4J_USER_ENV = 'NEO4J_USER'
    NEO4J_PASS_ENG = 'NEO4J_PASS'

    def __init__(self, *args, **kwargs):
        super(TestGraphQuery, self).__init__(*args, **kwargs)

        loginit = logging
        self.log = loginit.getLogger(__name__)

    def setUp(self):
        if self.NEO4J_HOST_PATH_ENV not in os.environ.keys() or \
                self.NEO4J_DOCKER_PATH_ENV not in os.environ.keys() or \
                self.NEO4J_BOLT_URL_ENV not in os.environ.keys() or \
                self.NEO4J_USER_ENV not in os.environ.keys() or \
                self.NEO4J_PASS_ENG not in os.environ.keys():
            raise Exception(' '.join(['Environment variables', self.NEO4J_HOST_PATH_ENV, 'and',
                                      self.NEO4J_DOCKER_PATH_ENV, 'and',
                                      self.NEO4J_BOLT_URL_ENV, 'and',
                                      self.NEO4J_USER_ENV, 'and',
                                      self.NEO4J_PASS_ENG, 'must be specified']))
        self.neo4j = Neo4jWorkflow(os.environ[self.NEO4J_BOLT_URL_ENV],
                                   os.environ[self.NEO4J_USER_ENV],
                                   os.environ[self.NEO4J_PASS_ENG],
                                   importHostDir=os.environ[self.NEO4J_HOST_PATH_ENV],
                                   importDir=os.environ[self.NEO4J_DOCKER_PATH_ENV])
        graphmlFile = open(testdir + "test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        try:
            self.gid = self.neo4j.import_workflow(graphml)
        except WorkflowError as wexc:
            self.log.error(wexc)

    def tearDown(self):
        self.log.info("Deleting graph %s", self.gid)
        if self.gid is not None:
            self.neo4j.delete_workflow(self.gid)

    def test_query_start_node(self):
        self.log.info("Testing searching for start node type.")
        d = self.neo4j.find_start_node(self.gid)
        self.assertIsNotNone(d, "Start node must be present")

    def test_query_find_node(self):
        self.log.info("Testing searching for node by id.")
        d = self.neo4j.find_node(self.gid, "Start")
        self.assertIsNotNone(d, "Start node must be present")
        d = self.neo4j.find_node(self.gid, "NoCopiesPledge")
        self.assertIsNotNone(d, "NoCopiesPledge node must be present")

    def test_query_adjacent(self):
        self.log.info("Testing searching for adjacent nodes")
        d = self.neo4j.find_adjacent_nodes(self.gid, "Start")
        self.assertEqual(len(d), 3, "Start node adjacent to three nodes")
        d = self.neo4j.find_adjacent_nodes(self.gid, "Start", "PI")
        self.assertEqual(len(d), 2, "Start node has two PI adjacent nodes")

    def test_query_reachable(self):
        self.log.info("Testing reachability for nodes")

        d = self.neo4j.find_reachable_nodes(self.gid, "Start", "IG")
        self.assertEqual(len(d), 1, "1 IG node reachable from start")

        d = self.neo4j.find_reachable_nodes(self.gid, "RestrictAccessPledge", "PI")
        self.assertEqual(len(d), 3, "3 IP nodes are reachable from RestrictAccessPledge")


if __name__ == '__main__':
    loginit = TestLogInitializer()
    unittest.main()
