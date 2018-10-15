from abc import ABC, abstractmethod

class AbstractWorkflow(ABC):

    @abstractmethod
    def import_workflow(self, graph: str, graphId: str = None) -> str:
        """ import graph from string giving it unique id
        (externally provided or auto-generated)"""
        return None

    @abstractmethod
    def validate_workflow(self, graphId: str) -> bool:
        pass

    @abstractmethod
    def delete_workflow(self, graphId: str) -> None:
        pass

    @abstractmethod
    def count_nodes(self, graphId: str, nodeRole: str = None) -> int:
        pass