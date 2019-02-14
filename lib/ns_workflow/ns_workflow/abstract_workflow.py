from abc import ABC, abstractmethod
from typing import List, Dict


class AbstractWorkflow(ABC):

    @abstractmethod
    def import_workflow(self, graph: str, graphId: str = None) -> str:
        """ import graph from string giving it unique id
        (externally provided or auto-generated)"""
        return None

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
    def find_start_node(self, graphId: str) -> str:
        """ return name of start node """
        return None

    @abstractmethod
    def find_node(selfs, graphId: str, nodeId: str) -> Dict[str, str]:
        """ return properties of specific nodes. graphs always have a 'Start' and 'Stop' nodes"""
        return None

    @abstractmethod
    def find_adjacent_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[str]:
        """ find names of adjacent nodes, optionally for a given role"""
        return None

    @abstractmethod
    def find_reachable_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[str]:
        """ find names of reachable nodes, optionally for a given role"""
        return None


class WorkflowError(Exception):
    def __init__(self, graphId: str, msg: str = None):
        if msg is None:
            msg = "Unspecified error in graph %s ", graphId
        else:
            msg = "Error %s in graph %s ", (msg, graphId)
        super(WorkflowError, self).__init__(msg)
        self.graphId = graphId


class WorkflowImportError(WorkflowError):
    """Error importing a workflow graph"""
    pass


class WorkflowQueryError(WorkflowError):
    """Error querying a workflow graph"""

    def __init__(self, graphId: str, nodeId: str, msg: str):
        msg = "%s in querying node %s", (msg, nodeId)
        super(WorkflowQueryError, self).__init__(graphId, msg)
        self.nodeId = nodeId
