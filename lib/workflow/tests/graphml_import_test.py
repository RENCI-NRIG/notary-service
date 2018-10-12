import unittest
import os
from ..graph_import.graphml import Neo4jWorkflow

class MyTestCase(unittest.TestCase):
    def test_convert_workflow(self):
        neo4j = Neo4jWorkflow("bolt://localhost:7687", "neo4j", "admin")
        graphmlFile = open("workflow/tests/test-graph.graphml", "r")
        graphml = graphmlFile.read()
        graphmlFile.close()
        id, filename = neo4j.prep_workflow(graphml, "NEW-ID")
        self.assertEqual(id, "NEW-ID")
        os.unlink(filename)

if __name__ == '__main__':
    unittest.main()
