from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any


class AbstractWorkflow(ABC):

    @abstractmethod
    def import_workflow(self, graph: str, graphId: str = None) -> str:
        """ import graph from string giving it unique id
        (externally provided or auto-generated)"""
        pass

    @abstractmethod
    def validate_workflow(self, graphId: str) -> None:
        """ validate graph according to a set of available rules"""
        pass

    @abstractmethod
    def delete_workflow(self, graphId: str) -> None:
        """ delete workflow graph from the store"""
        pass

    @abstractmethod
    def count_nodes(self, graphId: str, nodeRole: str = None) -> int:
        """ count the number of nodes in graph, with specific Role"""
        return 0

    @abstractmethod
    def node_exists(self, graphId: str, nodeId: str) -> bool:
        """ check if a node with this id exists """
        pass

    @abstractmethod
    def find_start_node(self, graphId: str) -> str:
        """ return name of start node """
        pass

    @abstractmethod
    def get_node_properties(selfs, graphId: str, nodeId: str) -> Dict[str, str]:
        """ return properties of specific nodes. graphs always have a 'Start' and 'Stop' nodes"""
        pass

    @abstractmethod
    def find_adjacent_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[Any]:
        """ find adjacent nodes, optionally for a given role """
        pass

    @abstractmethod
    def find_reachable_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[Any]:
        """ find reachable nodes, optionally for a given role """
        pass

    @abstractmethod
    def update_node_property(self, graphId: str, nodeId: str, propName: str, propVal: str) -> None:
        """ update a named property of a node, create if doesn't exist """
        pass

    @abstractmethod
    def create_child_node(self, graphId: str, nodeId: str, childNode: str) -> None:
        """ create a child node copying/inheriting properties of the parent """
        pass

    @abstractmethod
    def get_children(self, graphId: str, nodeId: str) -> List[str]:
        """ get a list of children nodes for this node """
        pass

    @abstractmethod
    def is_child_node(self, graphId: str, nodeId: str) -> bool:
        """ is this a child node """
        pass


class WorkflowError(Exception):
    def __init__(self, graphId: str, msg: Any = None):
        if msg is None:
            super(WorkflowError, self).__init__(("Unspecified error in graph %s " % graphId))
        else:
            super(WorkflowError, self).__init__(("Error %s in graph %s " % (msg, graphId)))
        self.graphId = graphId


class WorkflowImportError(WorkflowError):
    """Error importing a workflow graph"""
    pass


class WorkflowQueryError(WorkflowError):
    """Error querying a workflow graph"""

    def __init__(self, graphId: str, nodeId: str, msg: str):
        super(WorkflowQueryError, self).__init__(graphId, ("%s in querying node %s" % (msg, nodeId)))
        self.nodeId = nodeId
