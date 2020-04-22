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

        # add graph id to every node
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

    def _import_workflow(self, graphmlFile: str, graphId: str) -> None:
        """ import graph into Neo4j from a file"""

        try:
            with self.driver.session() as session:
                session.run(
                    'call apoc.import.graphml( $fileName, {batchSize: 10000, readLabels: true, storeNodeIds: true, defaultRelationshipType: "isPrerequisiteFor" } ) ',
                    fileName=graphmlFile)
                # force label on all imported nodes
                self.log.debug(f"Adding Node label to graph {graphId}")
                session.run('match (n {GraphID: $graphId }) set n:Node', graphId=graphId)
        except Exception as e:
            msg = "Neo4j APOC import error %s", str(e)
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
                self._import_workflow(mappedFileName, id)
                retry = -1
            except WorkflowImportError:
                self.log.warn("Transient error, unable to load, deleting and reimporting graph %s", id)
                retry = retry - 1
                self.delete_workflow(id)
                time.sleep(1.0)

        # remove the file
        os.unlink(hostFileName)

        if retry == 0:
            raise (WorkflowImportError(graphId, 'Unable to load graph after multiple attempts'))

        return id

    def _validate_workflow(self, graphId: str, rulesFile: str) -> None:
        """ validate the graph imported in Neo4j according to a set of given Cypher rules"""
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
        """ validate the graph imported in Neo4j according to standard Cypher rules """
        assert graphId is not None
        self.log.info('Validating workflow %s', graphId)
        return self._validate_workflow(graphId, os.path.dirname(__file__) + '/rules.json')

    def delete_workflow(self, graphId: str) -> None:
        """ delete a workflow with this ID from Neo4j"""
        assert graphId is not None
        self.log.debug('Deleting workflow %s', graphId)
        with self.driver.session() as session:
            session.run('match (n:Node {GraphID: $graphId })detach delete n', graphId=graphId)

    def count_nodes(self, graphId: str, nodeRole: str = None) -> int:
        """ count the nodes of particular role in workflow"""
        assert graphId is not None
        self.log.debug('Counting nodes in graph %s', graphId)
        with self.driver.session() as session:
            if nodeRole is None:
                return session.run('MATCH (n:Node {GraphID: $graphId }) RETURN count(n)',
                                   graphId=graphId).single().value()
            else:
                return session.run('MATCH (n:Node {GraphID: $graphId} ) WHERE $nodeRole IN split(n.Role, ",") RETURN count(n)',
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
        query = "MATCH (n:Node {GraphID: $graphId, Type: 'Start'}) RETURN properties(n)"
        assert graphId is not None
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId).single()
            if val is None:
                raise WorkflowQueryError(graphId, AbstractWorkflow.START, "Unable to find start node")
            return val.data()['properties(n)']

    def get_node_properties(self, graphId: str, nodeId: str) -> Dict[str, str]:
        """ get properties of a node with specific name in a graph """
        query = "MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) RETURN properties(n)"
        assert graphId is not None
        assert nodeId is not None
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId).single()
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find node")
            return val.data()['properties(n)']

    def find_adjacent_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[str]:
        """Get a list of nodes that are adjacent to the named node and optionally have a specific role
        See https://neo4j.com/docs/api/python-driver/current/types/graph.html for more info"""
        assert graphId is not None
        assert nodeId is not None
        if role is not None:
            query = "MATCH (:Node {GraphID: $graphId, ID: $nodeId}) -[:isPrerequisiteFor]-> (n:Node {GraphID: $graphId}) WHERE $role IN split(n.Role, ',') RETURN n.ID"
        else:
            query = "MATCH (:Node {GraphID: $graphId, ID: $nodeId}) -[:isPrerequisiteFor]-> (n:Node {GraphID: $graphId}) RETURN n.ID"
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, role=role)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find adjacent nodes")
            return val.value()

    def find_reachable_nodes(self, graphId: str, nodeId: str, role: str) -> List[str]:
        """Get a list of nodes reachable from the specified node and have a specific role.
        See https://neo4j.com/docs/api/python-driver/current/types/graph.html for more info"""
        assert graphId is not None
        assert nodeId is not None
        assert role is not None
        query = """MATCH (s:Node {GraphID: $graphId, ID: $nodeId}), (pi), p=(s) -[:isPrerequisiteFor*]-> (pi)
        WHERE $role IN split(pi.Role, ',') AND ALL(x in tail(reverse(tail(nodes(p)))) WHERE NOT $role IN split(x.Role, ',') ) WITH distinct(pi) AS dpi return dpi.ID"""

        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, role=role)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find reachable nodes")
            return val.value()

    def update_node_property(self, graphId: str, nodeId: str, propName: str, propVal: str) -> None:
        """ Use a cypher query to update or add a property to a node """
        assert graphId is not None
        assert nodeId is not None
        assert propName is not None
        query = "MATCH (s:Node {GraphID: $graphId, ID: $nodeId}) SET s+={ %s: $propVal} RETURN properties(s)" % propName
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, propVal=propVal)
            if val is None or len(val.value()) == 0:
                raise WorkflowQueryError(graphId, nodeId, "Unable to set property")
            pass

    def update_node_properties(self, graphId: str, nodeId: str, props: Dict[str, str]) -> None:
        """ update multiple properties at once """
        assert graphId is not None
        assert nodeId is not None
        assert props is not None

        allProps = ""
        for k, v in props.items():
            allProps += f'{k}: "{v}", '
        if len(allProps) > 2:
            allProps = allProps[:-2]

        query = "MATCH (s:Node {GraphID: $graphId, ID: $nodeId}) SET s+= { %s } RETURN properties(s)" % allProps
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None or len(val.value()) == 0:
                raise WorkflowQueryError(graphId, nodeId, "Unable to set properties")
            pass

    def create_child_node(self, graphId: str, nodeId: str, childNode: str) -> None:
        """ create a child node copying/inheriting properties of the parent """
        assert graphId is not None
        assert nodeId is not None
        assert childNode is not None

        # don't create children of child nodes
        if self.is_child_node(graphId, nodeId):
            raise WorkflowQueryError(graphId, nodeId, "Unable to create a child of child node")

        # using merge guarantees duplicates won't be created. copying properties ON CREATE
        # guarantees they will not be overwritten on existing node, however parent properties
        # are immutable anyway
        query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) MERGE (m:Node {GraphID:$graphId, ID:$childNode})
            -[:isChildOf]-> (n) ON CREATE SET m=n, m.ID=$childNode, m.SAFEType="user-set" RETURN m"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, childNode=childNode)
            if val is None or len(val.value()) == 0:
                raise WorkflowQueryError(graphId, nodeId, "Unable to create child node, node not found")
            pass

    def create_child_node_for_principal(self, graphId: str, nodeId: str, principalId: str) -> str:
        """ create a child node copying/inheriting properties of the parent, add principal property
        that carries principalId to the child. Name of child node is a concatenation of parent node
        id and principal id"""
        assert graphId is not None
        assert nodeId is not None
        assert principalId is not None

        # don't create children of child nodes
        if self.is_child_node(graphId, nodeId):
            raise WorkflowQueryError(graphId, nodeId, "Unable to create a child of child node")

        childNode = f"{nodeId}-{principalId}"

        # using merge guarantees duplicates won't be created. copying properties ON CREATE
        # guarantees they will not be overwritten on existing node, however parent properties
        # are immutable anyway
        query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) MERGE (m:Node {GraphID:$graphId, ID:$childNode})
            -[:isChildOf]-> (n) ON CREATE SET m=n, m.ID=$childNode, m.SAFEType="user-set", m.principal=$principalId RETURN m"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, childNode=childNode, principalId=principalId)
            if val is None or len(val.value()) == 0:
                raise WorkflowQueryError(graphId, nodeId, "Unable to create child node, node not found")
            pass
        return childNode

    def node_exists(self, graphId: str, nodeId: str) -> bool:
        """ check if a node exists """
        assert graphId is not None
        assert nodeId is not None

        query = "MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) RETURN n"
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None or len(val.value()) == 0:
                return False
            return True

    def get_children(self, graphId: str, nodeId: str) -> List[str]:
        """ get a list of children nodes for this node """
        assert graphId is not None
        assert nodeId is not None

        query = "MATCH (n:Node {GraphID: $graphId, ID: $nodeId}), (m) -[:isChildOf]-> (n) RETURN collect(m.ID)"
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find children")
            return val.value()[0]

    def is_child_node(self, graphId: str, nodeId: str) -> bool:
        """ is this node a child node """
        assert graphId is not None
        assert nodeId is not None

        query = "MATCH (n:Node {GraphID: $graphId, ID: $nodeId}), (n) -[:isChildOf]-> () RETURN count(n) > 0 AS result"
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to check for child relation")
            return val.value()[0]

    def is_conditional_node(self, graphId: str, nodeId: str) -> bool:
        """ is this a conditional node """
        assert graphId is not None
        assert nodeId is not None

        query = """MATCH (n:Node {GraphID:$graphId, ID: $nodeId, Type: "ConditionalAssertionItem"}) RETURN count(n) > 0"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to check if node is conditional")
            return val.value()[0]

    def find_adjacent_conditional_node(self, graphId: str, nodeId: str, parameterValue: str, role: str = None) -> str:
        assert graphId is not None
        assert nodeId is not None
        assert parameterValue is not None

        if role is not None:
            query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId, Type: "ConditionalAssertionItem"}) 
            -[r:isPrerequisiteFor {ParameterValue: $parameterValue}]-> (m:Node {GraphID: $graphId}) 
            WHERE $role IN split(m.Role, ',') RETURN m.ID"""
        else:
            query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId, Type: "ConditionalAssertionItem"}) 
            -[r:isPrerequisiteFor {ParameterValue: $parameterValue}]-> (m:Node {GraphID: $graphId}) RETURN m.ID"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, role=role, parameterValue=parameterValue)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find conditional successor")
            myVal = val.value()
            if len(myVal) > 0:
                return myVal[0]
            else:
                return None

    def find_fan_out_parent(self, graphId: str, nodeId: str) ->str:
        """ find the nearest fan-out node (or Start) """
        assert graphId is not None
        assert nodeId is not None

        query = """MATCH path = (p:Node {GraphID: $graphId}) -[:isPrerequisiteFor*]-> (c:Node {GraphID: $graphId, ID: $nodeId})
            <-[:isPrerequisiteFor*]- (p:Node {GraphID: $graphId}) RETURN p.ID ORDER BY length(path) LIMIT 1"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find common completed parent")
            myVal = val.value()
            if len(myVal) > 0:
                return myVal[0]
            else:
                return None

    def find_immediate_common_set_parent_nodes(self, graphId: str, nodeId: str) ->List[str]:
        """ find immediate parent nodes, skipping template-user-set nodes """

        assert graphId is not None
        assert nodeId is not None

        query = """match (n:Node {GraphID: $graphId, ID: $nodeId}) <-[:isPrerequisiteFor]-
           (ip:Node {GraphID: $graphId, SAFEType: "template-user-set"}) <-[:isPrerequisiteFor*]- (p1:Node {GraphID: $graphId, SAFEType: "common-set"})
           WITH p1 MATCH (p1)-[:isPrerequisiteFor]-> (m:Node {GraphID: $graphId, SAFEType: "template-user-set"})
           RETURN DISTINCT p1.ID as id UNION
           MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) <-[:isPrerequisiteFor]- (p2:Node {GraphID: $graphId, SAFEType: "common-set"})
           RETURN p2.ID as id"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to find common completed parent")
            return val.value()

    def list_not_completed_common_set(self, graphId: str) -> bool:
        """ list all common set nodes that haven't been completed """

        assert graphId is not None

        query = """MATCH (n:Node {GraphID: $graphId, SAFEType: "common-set"}) 
        WHERE NOT exists(n.completed) OR n.completed <> "True"  RETURN collect(n.ID) as id"""

        with self.driver.session() as session:
            val = session.run(query, graphId=graphId)
            if val is None:
                raise WorkflowQueryError(graphId, None, "Unable to list incomplete common-set")
            myVal = val.value()
            if len(myVal) > 0:
                return myVal[0]
            else:
                return None

    def list_conditional_options(self, graphId: str, nodeId: str) ->List[str]:

        assert graphId is not None
        assert nodeId is not None

        if not self.is_conditional_node(graphId, nodeId):
            raise WorkflowQueryError(graphId, nodeId, "Is not a conditional node - unable to make selection")

        query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) -[r:isPrerequisiteFor]-> (m) 
        RETURN r.ParameterValue"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to retrieve list of options")
            return val.value()

    def make_conditional_selection_and_disable_branches(self, graphId: str, nodeId: str, value: str) ->None:

        assert graphId is not None
        assert nodeId is not None
        assert value is not None

        lval = self.list_conditional_options(graphId, nodeId)

        if value not in lval:
            raise WorkflowQueryError(graphId, nodeId, f"Unable to set value {value} - it is not one of the available options {lval}")

        self.update_node_property(graphId, nodeId, AbstractWorkflow.PARAMETER_VALUE_FIELD, value)

        query = """MATCH (n:Node {GraphID: $graphId, ID: $nodeId}) -[r:isPrerequisiteFor]-> (m:Node {GraphID: $graphId}) 
        WHERE r.ParameterValue <> $value 
        CREATE (n) -[r2:isNotSelectedPrerequisiteFor]-> (m) SET r2=r 
        WITH r DELETE r"""
        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId, value=value)
            if val is None:
                raise WorkflowQueryError(graphId, nodeId, "Unable to relabel not selected conditional branches")
            return val.value()

    def is_reachable_from_start(self, graphId: str, nodeId: str) ->bool:

        assert graphId is not None
        assert nodeId is not None

        query = """MATCH p=(n:Node {GraphID: $graphId, ID: "Start"}) -[q:isPrerequisiteFor*1..]-> 
        (m:Node {GraphID: $graphId, ID: $nodeId}) RETURN count(p) > 0"""

        with self.driver.session() as session:
            val = session.run(query, graphId=graphId, nodeId=nodeId)
            if val is None:
                raise WorkflowQueryError(graphId, None, "Unable to determine reachability")
            myVal = val.value()
            if len(myVal) > 0:
                return myVal[0]
            else:
                return None
