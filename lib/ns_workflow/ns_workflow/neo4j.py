# from workflow.graph.abstract_workflow import AbstractWorkflow, WorkflowError, WorkflowImportError, WorkflowQueryError
import json
import logging
import os
import tempfile
import time
import uuid
from typing import Any, List, Dict, Tuple

import neo4j
import networkx as nx
from neo4j import GraphDatabase

from .abstract_workflow import AbstractWorkflow, WorkflowImportError, WorkflowQueryError

APOCRetryCount = 10


class Neo4jWorkflow(AbstractWorkflow):

    def __init__(self, url: str, user: str, pswd: str, importHostDir: str = None, importDir: str = None) -> None:
        """ URL of Neo4j instance, credentials and directory
        from where Neo4j can import graphs"""
        self.url = url
        self.user = user
        self.pswd = pswd
        self.importHostDir = importHostDir
        self.importDir = importDir
        self.driver = GraphDatabase.driver(self.url, auth=(user, pswd))

        self.log = logging.getLogger(__name__)

    def _prep_workflow(self, graphml: str, graphId: str = None) -> Tuple[str, str, str]:
        """Import a workflow graphml, assigning it a new unique graph ID
        return the name of the file where graph is saved with updated GraphID
        and the assigned graphID"""
        if graphId is None:
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
        # where to save is determined by whether importDir is set
        destDir = self.importHostDir
        if self.importHostDir is None:
            destDir = tempfile.gettempdir()

        uniqName = str(uuid.uuid4())
        hostFileName = os.path.join(destDir, uniqName)
        mappedFileName = os.path.join(self.importDir, uniqName)

        nx.write_graphml(g, hostFileName)

        return graphId, hostFileName, mappedFileName

    def _import_workflow(self, graphmlFile: str) -> None:
        """ import graph into Neo4j from a file"""

        try:
            with self.driver.session() as session:
                session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, readLabels: true, storeNodeIds: true, defaultRelationshipType: "isPrerequisiteFor" } ) ',
                    fileName=graphmlFile)
        except Exception as e:
            msg = "Neo4j APOC error %s", str(e)
            raise WorkflowImportError(None, msg)

    def import_workflow(self, graphml: str, graphId: str = None) -> str:
        """ import graph into Neo4j from a string, assigning it a unique id"""
        assert graphml is not None

        self.log.debug('Importing workflow with id %s', graphId)
        try:
            id, hostFileName, mappedFileName = self._prep_workflow(graphml, graphId)
        except Exception as e:
            msg = "NetworkX graph error %s", str(e)
            raise WorkflowImportError(graphId, msg)

        if graphId is not None:
            assert (id == graphId)

        retry = APOCRetryCount
        while retry > 0:
            try:
                """ something in APOC prevents loading sometimes """
                self.log.debug("Trying to load the file")
                self._import_workflow(mappedFileName)
                retry = -1
            except WorkflowImportError:
                self.log.error("Unable to load, deleting graph %s", id)
                self.delete_workflow(id)
                retry = retry - 1
                time.sleep(1.0)

        # remove the file
        os.unlink(hostFileName)

        if retry == 0:
            raise (WorkflowImportError(graphId, 'Unable to load graph'))

        return id

    def _validate_workflow(self, graphId: str, rulesFile: str) -> None:
        """ validate the graph imported in Neo4j according to a set of given Cipher rules"""
        f = open(rulesFile)
        rulesDict = json.load(f)
        f.close()

        for r in rulesDict:
            with self.driver.session() as session:
                # print('Applying rule ', r['msg'])
                v = session.run(r['rule'], graphId=graphId).single().value()
                # print("Rule {}, value {}".format(r['msg'], v))
                if v is False:
                    raise WorkflowImportError(graphId, r['msg'])

        return True

    def validate_workflow(self, graphId: str) -> None:
        """ validate the graph imported in Neo4j according to standard Cipher rules """
        assert graphId is not None
        self.log.info('Validating workflow %s', graphId)
        return self._validate_workflow(graphId, os.path.dirname(__file__) + '/rules.json')

    def delete_workflow(self, graphId: str) -> None:
        """ delete a workflow with this ID from Neo4j"""
        assert graphId is not None
        self.log.debug('Deleting workflow %s', graphId)
        with self.driver.session() as session:
            session.run('match (n {GraphID: $graphId })detach delete n', graphId=graphId)

    def count_nodes(self, graphId: str, nodeRole: str = None) -> int:
        """ count the nodes of particular role in workflow"""
        assert graphId is not None
        self.log.debug('Counting nodes in graph %s', graphId)
        with self.driver.session() as session:
            if nodeRole is None:
                return session.run('match (n {GraphID: $graphId }) return count(n)',
                                   graphId=graphId).single().value()
            else:
                return session.run('match (n {GraphID: $graphId, Role: $nodeRole} ) return count(n)',
                                   graphId=graphId, nodeRole=nodeRole).single().value()

    def _run_node_dict_query(self, graphId: str, nodeId: str, query: str) -> Dict[str, str]:
        """ run a query returning a dictionary starting from a specific node"""
        with self.driver.session() as session:
            if query is not None:
                return session.run(query, graphId=graphId, nodeId=nodeId).single().asMap()

    def _run_node_list_query(self, graphId: str, nodeId: str, query: str) -> List[Any]:
        """ run a query returning a list starting from a specific node"""
        with self.driver.session() as session:
            if query is not None:
                return session.run(query, graphId=graphId, nodeId=nodeId).list()

    def find_start_node(self, graphId: str) -> Dict[str, str]:
        """ find start node in a graph and return its properties """
        query = "match (n {GraphID: $graphId, Type: 'Start'}) return properties(n)"
        assert graphId is not None
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId).single()
            if val is None:
                raise WorkflowQueryError(graphId, "Start", "Unable to find start node")
            return val.data()['properties(n)']

    def find_node(self, graphId: str, nodeId: str) -> Dict[str, str]:
        """ get properties of a node with specific name in a graph """
        query = "match (n {GraphID: $graphId, ID: $nodeId}) return properties(n)"
        assert graphId is not None
        assert nodeId is not None
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId).single()
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find node")
            return val.data()['properties(n)']

    def find_adjacent_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[neo4j.types.graph.Node]:
        """Get a list of nodes that are adjacent to the named node and optionally have a specific role
        See https://neo4j.com/docs/api/python-driver/current/types/graph.html for more info"""
        assert graphId is not None
        assert nodeId is not None
        if role is not None:
            query = "match ({GraphID: $graphId, ID: $nodeId}) --> (n) where n.Role=$role return n"
        else:
            query = "match ({GraphID: $graphId, ID: $nodeId}) --> (n) return n"
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, role=role)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find adjacent nodes")
            return val.value()

    def find_reachable_nodes(self, graphId: str, nodeId: str, role: str) -> List[neo4j.types.graph.Node]:
        """Get a list of nodes reachable from the specified node and have a specific role.
        See https://neo4j.com/docs/api/python-driver/current/types/graph.html for more info"""
        assert graphId is not None
        assert nodeId is not None
        assert role is not None
        query = "match (s {GraphID: $graphId, ID: $nodeId}), (pi {Role: $role}), p=(s) -[*]-> (pi) where ALL(x in tail(reverse(tail(nodes(p)))) where not x.Role=$role) return distinct(pi)"

        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, role=role)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find reachable nodes")
            return val.value()
