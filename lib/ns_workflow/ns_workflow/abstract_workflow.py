from abc import ABC, abstractmethod
from typing import List, Dict, Tuple, Any, Set
import logging


class AbstractWorkflow(ABC):

    COMPLETED_FIELD = "completed"
    COMPLETED_VALUE = "True"

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
    def find_adjacent_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[str]:
        """ find adjacent nodes, optionally for a given role """
        pass

    @abstractmethod
    def find_adjacent_conditional_node(self, graphId: str, nodeId: str, parameterValue: str, role: str = None) -> str:
        """ return the id of the node which follows id the condition specified by
        parameter value is satisfied """
        pass

    @abstractmethod
    def find_reachable_nodes(self, graphId: str, nodeId: str, role: str = None) -> List[str]:
        """ find reachable nodes, optionally for a given role """
        pass

    @abstractmethod
    def update_node_property(self, graphId: str, nodeId: str, propName: str, propVal: str) -> None:
        """ update a named property of a node, create if doesn't exist """
        pass

    @abstractmethod
    def update_node_properties(self, graphId: str, nodeId: str, props: Dict[str, str]) -> None:
        """ update multiple properties """
        pass

    @abstractmethod
    def create_child_node(self, graphId: str, nodeId: str, childNode: str) -> None:
        """ create a child node copying/inheriting properties of the parent """
        pass

    @abstractmethod
    def create_child_node_for_principal(self, graphId: str, nodeId: str, principalId: str) -> str:
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

    @abstractmethod
    def is_conditional_node(self, graphId: str, nodeId: str) ->bool:
        """ is this a conditional node """
        pass

    @abstractmethod
    def find_fan_out_parent(self, graphId: str, nodeId: str) ->str:
        """ find the nearest fan-out (conditional or not) parent of this node """
        pass

    @abstractmethod
    def find_immediate_common_set_parent_nodes(self, graphId: str, nodeId: str) ->List[str]:
        """ find immediate parent nodes, skipping template-user-set nodes """
        pass

    def save_safe_token_and_complete(self, graphId: str, nodeId: str, token: str) -> None:
        """ save the token and mark the node as done """
        props = { "SAFEToken": token, self.COMPLETED_FIELD: self.COMPLETED_VALUE}

        self.update_node_properties(graphId, nodeId, props)

    def is_node_completed(self, graphId: str, nodeId: str) ->bool:
        props = self.get_node_properties(graphId, nodeId)
        if nodeId == "Start":
            return True

        if self.COMPLETED_FIELD in props and props[self.COMPLETED_FIELD] == self.COMPLETED_VALUE:
            return True
        return False

    def check_fan_in_complete(self, graphId: str, nodeId: str) ->bool:
        """ check if the fan-in of this node (conditional or not) is completed """

        # find the nearest fan-out parent
        fanOutParent = self.find_fan_out_parent(graphId, nodeId)

        if fanOutParent is None:
            # this isn't a fan-in node
            raise WorkflowQueryError(graphId, nodeId, "This node is not a fan-in node")

        # check if it is completed
        if not self.is_node_completed(graphId, fanOutParent):
            # fan in can't complete until at least fan-out parent is complete
            return False

        if self.is_conditional_node(graphId, fanOutParent):
            # only one branch leads to nodeId, and parent is done
            # therefore we're done
            return True
        else:
            # check all branches of unconditional fan-out
            parentsDone = True
            for parent in self.find_immediate_common_set_parent_nodes(graphId, nodeId):
                parentProps = self.get_node_properties(graphId, parent)
                if self.COMPLETED_FIELD not in parentProps  or \
                    parentProps[self.COMPLETED_FIELD] != self.COMPLETED_VALUE:
                    parentsDone = False
                    break
            return parentsDone

    def find_reachable_not_completed_nodes(self, principalId: str, role: str, graphId: str, nodeId: str,
        incompleteNodeSet: Set[str], logger=None) -> None:
        """ meant to be executed recursively from 'Start' node with an empty incompleteNodeSet.
        note that the function will create children of template-user-set nodes and add them to the
        returned list """

        logger is not None and logger.info(f"Visiting node {nodeId}")

        props = self.get_node_properties(graphId, nodeId)

        if props is None:
            raise WorkflowError(f"Node {nodeId} does not have any properties")

        if props["Type"] == "Start":
            for n in self.find_adjacent_nodes(graphId, nodeId):
                # recursive call to all nodes from Start
                self.find_reachable_not_completed_nodes(principalId, role, graphId, n, incompleteNodeSet, logger)
            return
        elif props["Type"] == "Stop":
            return
        elif props["Type"] == "AssertionItem":
            if self.COMPLETED_FIELD in props and props[self.COMPLETED_FIELD] == self.COMPLETED_VALUE:
                logger is not None and logger.info(f"  Node is completed")
                # node is completed, continue the traversal
                if self.is_conditional_node(graphId, nodeId):
                    logger is not None and logger.info(f"    Node is conditional")
                    # if node is conditional, follow the branch based on ParameterValue
                    newNodeId = self.find_adjacent_conditional_node(graphId, nodeId, props["ParameterValue"])
                    if newNodeId is not None:
                        self.find_reachable_not_completed_nodes(principalId, role, graphId, newNodeId, incompleteNodeSet, logger)
                else:
                    logger is not None and logger.info(f"    Node is not conditional, following fanout")
                    # otherwise follow the fan-out
                    for n in self.find_adjacent_nodes(graphId, nodeId):
                        self.find_reachable_not_completed_nodes(principalId, role, graphId, n, incompleteNodeSet, logger)
                return
            # this node is not completed
            logger is not None and logger.info(f"  Node is NOT completed")
            if not role in props['Role'].split(','):
                # if SAFEType is template-user-set and role doesn't match ours, keep traversing
                logger is not None and logger.info(f"  Node role {props['Role']}, doesn't match ours {role}")
                if props["SAFEType"] == 'template-user-set':
                    # this node cannot have a fan-out (conditional or not)
                    # find the next node and keep going
                    logger is not None and logger.info(f"    Node is a template-user-set, skipping")
                    for n in self.find_adjacent_nodes(graphId, nodeId):
                        self.find_reachable_not_completed_nodes(principalId, role, graphId, n, incompleteNodeSet, logger)
                # otherwise we stop here
                return
            else:
                # role matches our own
                logger is not None and logger.info(f"  Node role {role} matches ours")
                if props["SAFEType"] == 'common-set':
                    logger is not None and logger.info(f"  Node is a common-set node, checking fan-in")
                    # if it IS a fan-in node, check fan-in parents (conditional or not) before adding
                    # it not a fan-in, add
                    fanInComplete = False
                    try:
                        fanInComplete = self.check_fan_in_complete(graphId, nodeId)
                    except WorkflowQueryError as err:
                        # single-branch
                        fanInComplete = True
                    logger is not None and logger.info(f"  Node fan in is {fanInComplete}, adding")
                    if fanInComplete:
                        incompleteNodeSet.add(nodeId)
                elif props["SAFEType"] == 'template-user-set':
                    logger is not None and logger.info(f"  Node {nodeId} has type template-user-set, creating child for principal {principalId}")
                    childNodeId = self.create_child_node_for_principal(graphId, nodeId, principalId)
                    childProps = self.get_node_properties(graphId, childNodeId)
                    if self.COMPLETED_FIELD in childProps and \
                        childProps[self.COMPLETED_FIELD] == self.COMPLETED_VALUE:
                        logger is not None and logger.info(f"  Child node is completed, follow fan-out")
                        # child is completed, fan-out is not allowed on template-user-set nodes,
                        # just follow to the next node
                        for n in self.find_adjacent_nodes(graphId, nodeId):
                            self.find_reachable_not_completed_nodes(principalId, role, graphId, n, incompleteNodeSet, logger)
                    else:
                        logger is not None and logger.info(f"  Child is not completed, checking fan-in")
                        # if child not completed, check for fan-in and add
                        fanInComplete = False
                        try:
                            fanInComplete = self.check_fan_in_complete(graphId, nodeId)
                        except WorkflowQueryError as err:
                            # single branches
                            fanInComplete = True
                        logger is not None and logger.info(f"  Node fan in is {fanInComplete}, adding")
                        if fanInComplete:
                            incompleteNodeSet.add(childNodeId)

        return

    def is_workflow_complete(self, principalId: str, role: str, graphId: str, logger=None) -> bool:
        """ determine if workflow has been completed for a given principal and role """

        # check if common-set is completed
        cs = self.list_not_completed_common_set(graphId)

        logger is not None and logger.info(f"Common set is {cs}")
        if cs is not None and len(cs) > 0:
            return False

        logger is not None and logger.info(f"Checking user-set now")
        # see if there are any reachable (only user-set would be left) nodes for id, role tuple
        userSet = set()
        self.find_reachable_not_completed_nodes(principalId, role, graphId, "Start", userSet, None)

        logger is not None and logger.info(f"User set is {userSet}")

        if userSet is None or len(userSet) == 0:
            return True

    @abstractmethod
    def list_not_completed_common_set(self, graphId: str) -> bool:
        """ list all common set nodes that haven't been completed """
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
