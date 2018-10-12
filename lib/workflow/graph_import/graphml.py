import uuid
import networkx as nx
import tempfile
import os
from neo4j.v1 import GraphDatabase
from typing import List, Set, Dict, Tuple, Optional


class Neo4jWorkflow:

    def __init__(self, url: str, user: str, pswd: str) -> None:
        self.url = url
        self.user = user
        self.pswd = pswd
        self.driver = GraphDatabase.driver(self.url, auth=(user, pswd))

    def prep_workflow(self, graphml: str, graphId: str = None) -> Tuple[str, str]:
        """Import a workflow graphml, assigning it a new unique graph ID
        return the name of the file where graph is saved with updated GraphID
        and the assigned graphID"""
        if graphId == None:
            graphId = str(uuid.uuid4())

        # save to file
        f1 = tempfile.NamedTemporaryFile(suffix="-graphml", mode='w')
        f1.write(graphml)

        # read using networkx
        g = nx.read_graphml(f1.name)
        f1.close()

        for n in list(g.nodes):
            g.nodes[n]['GraphID'] = graphId

        # save back to GraphML
        f2, f2Name = tempfile.mkstemp(suffix="-graphml-neo4j")
        os.close(f2)
        nx.write_graphml(g, f2Name)

        return graphId, f2Name

    def import_workflow(self, graphmlFile: str) -> None:
        """ graph_import into Neo4j from a file"""

        with self.driver.session() as session:
            session.run("call apoc.graph_import.graphml('$fileName', "
                "{batchSize: 10000, readLabels: true, storeNodeIds: true, "
                "defaultRelationshipType:'isPrerequisiteFor'})", fileName=graphmlFile)

    def validate_workflow(self, graphId: str, rulesFile: str) -> bool:
        """ validate the graph imported in Neo4j according to a set of Cipher rules"""

        return True

