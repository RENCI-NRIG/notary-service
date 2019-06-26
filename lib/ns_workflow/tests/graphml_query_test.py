import logging
import os
import unittest

from ns_workflow import Neo4jWorkflow, WorkflowError, WorkflowQueryError, AbstractWorkflow

global testdir
testdir = os.path.dirname(os.path.dirname(__file__)) + '/tests/'


class TestGraphQuery(unittest.TestCase):
    NEO4J_IMPORTS_PATH_HOST_ENV = 'NEO4J_IMPORTS_PATH_HOST'
    NEO4J_IMPORTS_PATH_DOCKER_ENV = 'NEO4J_IMPORTS_PATH_DOCKER'
    NEO4J_BOLT_URL_ENV = 'NEO4J_BOLT_URL'
    NEO4J_USER_ENV = 'NEO4J_USER'
    NEO4J_PASS_ENV = 'NEO4J_PASS'

    def __init__(self, *args, **kwargs):
        super(TestGraphQuery, self).__init__(*args, **kwargs)

        self.log = logging.getLogger(__name__)

    def setUp(self):
        if self.NEO4J_IMPORTS_PATH_HOST_ENV not in os.environ.keys() or \
                self.NEO4J_IMPORTS_PATH_DOCKER_ENV not in os.environ.keys() or \
                self.NEO4J_BOLT_URL_ENV not in os.environ.keys() or \
                self.NEO4J_USER_ENV not in os.environ.keys() or \
                self.NEO4J_PASS_ENV not in os.environ.keys():
            raise Exception(' '.join(['Environment variables', self.NEO4J_IMPORTS_PATH_HOST_ENV, 'and',
                                      self.NEO4J_IMPORTS_PATH_DOCKER_ENV, 'and',
                                      self.NEO4J_BOLT_URL_ENV, 'and',
                                      self.NEO4J_USER_ENV, 'and',
                                      self.NEO4J_PASS_ENV, 'must be specified']))
        self.neo4j = Neo4jWorkflow(os.environ[self.NEO4J_BOLT_URL_ENV],
                                   os.environ[self.NEO4J_USER_ENV],
                                   os.environ[self.NEO4J_PASS_ENV],
                                   importHostDir=os.environ[self.NEO4J_IMPORTS_PATH_HOST_ENV],
                                   importDir=os.environ[self.NEO4J_IMPORTS_PATH_DOCKER_ENV])
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

    #@unittest.skip("Skip")
    def test_query_start_node(self):
        self.log.info("Testing searching for start node type.")
        d = self.neo4j.find_start_node(self.gid)
        self.assertIsNotNone(d, "Start node must be present")

    #@unittest.skip("Skip")
    def test_query_get_node_properties(self):
        self.log.info("Testing searching for node by id.")
        d = self.neo4j.get_node_properties(self.gid, "Start")
        self.assertIsNotNone(d, "Start node must be present")
        d = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.assertIsNotNone(d, "NoCopiesPledge node must be present")

    #@unittest.skip("Skip")
    def test_query_adjacent(self):
        self.log.info("Testing searching for adjacent nodes")
        d = self.neo4j.find_adjacent_nodes(self.gid, "Start")
        self.assertEqual(len(d), 6, "Start node adjacent to six nodes")
        self.log.info(d)
        d = self.neo4j.find_adjacent_nodes(self.gid, "Start", AbstractWorkflow.ROLE_PI)
        self.assertEqual(len(d), 6, "Start node has six PI adjacent nodes")
        self.log.info(d)

    #@unittest.skip("Skip")
    def test_query_reachable(self):
        self.log.info("Testing reachability for nodes")

        d = self.neo4j.find_reachable_nodes(self.gid, "Start", AbstractWorkflow.ROLE_IG)
        self.assertEqual(len(d), 1, "1 IG node reachable from start")

        d = self.neo4j.find_reachable_nodes(self.gid, "RestrictAccessPledge", AbstractWorkflow.ROLE_PI)
        self.log.info(f"PI nodes reachable from RestrictAccessPledge are {d}")
        self.assertEqual(len(d), 1, "1 PI nodes are reachable from RestrictAccessPledge")

    #@unittest.skip("Skip")
    def test_update_property(self):
        self.log.info("Testing update property")

        self.neo4j.update_node_property(self.gid, "NoCopiesPledge", "NewProperty", "NewValue")
        d = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.assertTrue(d["NewProperty"] == "NewValue")
        with self.assertRaises(WorkflowQueryError):
            self.neo4j.update_node_property(self.gid, "BogusNode", "NewProperty", "NewValue")

    def test_update_properties(self):
        self.log.info("Testing setting multiple properties")

        props = {"someProp": "someVal", "someOtherProp": "someOtherVal"}
        self.neo4j.update_node_properties(self.gid, "NoCopiesPledge", props)
        d = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.assertTrue(d["someProp"] == "someVal")
        self.assertTrue(d["someOtherProp"] == "someOtherVal")
        props = {"someProp": "someVal", "someOtherProp": "changedVal"}
        self.neo4j.update_node_properties(self.gid, "NoCopiesPledge", props)
        d = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.assertTrue(d["someProp"] == "someVal")
        self.assertTrue(d["someOtherProp"] == "changedVal")

    def test_save_safe_token_and_complete(self):
        self.log.info("Testing saving token and marking node complete")
        self.neo4j.save_safe_token_and_complete(self.gid, "NoCopiesPledge", "ABCDEFG", "Bob")
        self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        d = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.log.info(d)
        self.assertTrue(d["completed"] == "True")
        self.assertTrue(d["SAFEToken"] == "ABCDEFG")

    #@unittest.skip("Skip")
    def test_create_child(self):
        self.log.info("Testing adding a child node")

        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "BobsPledge")
        d1 = self.neo4j.get_node_properties(self.gid, "BobsPledge")
        self.log.info(d1)
        d2 = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.log.info(d2)
        self.assertTrue(d1["ID"] == "BobsPledge")
        self.assertTrue(len(d1) == len(d2))

        with self.assertRaises(WorkflowQueryError):
            self.neo4j.create_child_node(self.gid, "BobsPledge", "InvalidChild")

    def test_create_child_for_principal(self):
        self.log.info("Testing adding a child node for principal")

        childNode = self.neo4j.create_child_node_for_principal(self.gid, "NoCopiesPledge", "Bob")
        d1 = self.neo4j.get_node_properties(self.gid, childNode)
        self.log.info(d1)
        d2 = self.neo4j.get_node_properties(self.gid, "NoCopiesPledge")
        self.log.info(d2)
        self.assertTrue(d1["ID"] == "NoCopiesPledge-Bob")
        self.assertTrue(d1["principal"] == "Bob")
        self.assertTrue(len(d1) == len(d2) + 1)

    #@unittest.skip("Skip")
    def test_node_exists(self):
        self.log.info("Testing node existst")

        self.assertTrue(self.neo4j.node_exists(self.gid, "NoCopiesPledge"))
        self.assertFalse(self.neo4j.node_exists(self.gid, "Blah"))

    def test_get_children(self):
        self.log.info("Testing getting children")

        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "BobsPledge")
        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "AlicesPledge")
        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "AlicesPledge")

        d = self.neo4j.get_children(self.gid, "NoCopiesPledge")
        self.assertTrue(len(d) == 2)

        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "AlansPledge")
        d = self.neo4j.get_children(self.gid, "NoCopiesPledge")
        self.assertTrue(len(d) == 3)

    def test_is_child(self):
        self.log.info("Testing testing for child")

        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "BobsPledge")
        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "AlicesPledge")
        self.neo4j.create_child_node(self.gid, "NoCopiesPledge", "AlicesPledge")

        d = self.neo4j.is_child_node(self.gid, "NoCopiesPledge")
        self.assertFalse(d)
        d = self.neo4j.is_child_node(self.gid, "BobsPledge")
        self.assertTrue(d)

    def test_is_conditional_node(self):
        self.log.info("Testing is_conditional_node")

        b = self.neo4j.is_conditional_node(self.gid, "ServerOrWorkstation")
        self.assertTrue(b)
        b = self.neo4j.is_conditional_node(self.gid, "ServerUsedInOtherProjects")
        self.assertFalse(b)

    def test_list_conditional_options(self):
        self.log.info("Testing get conditional options")

        b = self.neo4j.list_conditional_options(self.gid, "ServerOrWorkstation")
        self.log.info(f"Conditional options: {b}")
        self.assertTrue('Workstation' in b and 'Server' in b)

    def test_make_conditional_selection_and_disable_branches(self):
        self.log.info("Testing marking a conditional selection and disabling branches")

        an = self.neo4j.find_adjacent_nodes(self.gid, "ServerOrWorkstation")
        self.log.info(f"Initially adjacent are {an}")
        self.assertTrue(len(an) == 2)
        self.assertTrue(self.neo4j.is_reachable_from_start(self.gid, "ServerUsedInOtherProjects"))
        self.assertTrue(self.neo4j.is_reachable_from_start(self.gid, "WorkstationSecurityProtocols"))
        self.neo4j.make_conditional_selection_and_disable_branches(self.gid, "ServerOrWorkstation", "Workstation")
        an = self.neo4j.find_adjacent_nodes(self.gid, "ServerOrWorkstation")
        self.log.info(f"After selection adjacent are {an}")
        self.assertTrue(len(an) == 1)
        self.assertFalse(self.neo4j.is_reachable_from_start(self.gid, "ServerUsedInOtherProjects"))
        self.assertTrue(self.neo4j.is_reachable_from_start(self.gid, "WorkstationSecurityProtocols"))

        with self.assertRaises(WorkflowQueryError):
            self.neo4j.make_conditional_selection_and_disable_branches(self.gid, "ServerOrWorkstation", "BogusValue")

    def test_find_fan_out_parent(self):
        self.log.info("Testing finding common completed parent")

        d = self.neo4j.find_fan_out_parent(self.gid, "PrintEnvironment")
        self.log.info(f"Common parent is {d}")
        self.assertTrue(d is not None and d == "Start")

        # test that there isn't a common completed parent here, until ServerOWorkstation is
        # completed
        d = self.neo4j.find_fan_out_parent(self.gid, "WorkstationSecurityProtocols")
        self.log.info(f"Fan-out parent of WorkstationSecurityProtocols is {d}")
        self.assertTrue(d == "ServerOrWorkstation")

    def test_find_immediate_common_set_parent_nodes(self):
        self.log.info("Testing finding common-set parents")

        d = self.neo4j.find_immediate_common_set_parent_nodes(self.gid, "PrintEnvironment")
        self.log.info(f"Common-set parents of PrintEnvironment are {d}")
        self.assertTrue(d is not None and 'TemporaryFilesPeriodicRemovalPledge' in d
          and 'CodeBackupSelectionPledge' in d and 'NoCopiesPledge' in d)
        self.assertTrue(len(d) == 3)

        d = self.neo4j.find_immediate_common_set_parent_nodes(self.gid, "WorkstationSecurityProtocols")
        self.log.info(f"Common-set parents of WorkstationSecurityProtocols are {d}")

        self.assertTrue(d is not None and 'ServerSecurityProtocols' in d
          and 'ServerOrWorkstation' in d)
        self.assertTrue(len(d) == 2)

        d = self.neo4j.find_immediate_common_set_parent_nodes(self.gid, "IRBAbidePledge")
        self.assertTrue(d is not None and 'IRBSubmitted' in d)
        self.assertTrue(len(d) == 1)

    def test_check_fan_in_complete(self):
        self.log.info("Testing fan-in complete functionality")

        self.log.info("Single branch exception")
        with self.assertRaises(WorkflowQueryError):
            self.neo4j.check_fan_in_complete(self.gid, "PaymentMade")

        self.log.info("Unconditional fan-out")
        # test unconditional fan-out
        d = self.neo4j.check_fan_in_complete(self.gid, "PrintEnvironment")
        self.assertFalse(d)
        self.neo4j.save_safe_token_and_complete(self.gid, "TemporaryFilesPeriodicRemovalPledge", "ABCD", "Bob")
        self.neo4j.save_safe_token_and_complete(self.gid, "CodeBackupSelectionPledge", "ABCD", "Bob")
        self.neo4j.save_safe_token_and_complete(self.gid, "NoCopiesPledge", "ABCD", "Bob")
        d = self.neo4j.check_fan_in_complete(self.gid, "PrintEnvironment")
        self.assertTrue(d)

        self.neo4j.save_safe_token_and_complete(self.gid, "PrintEnvironment", "ABCD", "Bob")
        d = self.neo4j.check_fan_in_complete(self.gid, "HardcopyDiscardPledge")
        self.assertFalse(d)

        self.neo4j.save_safe_token_and_complete(self.gid, "SplitPledge1", "ABCDEFG", "Bob")
        d = self.neo4j.check_fan_in_complete(self.gid, "HardcopyDiscardPledge")
        self.assertFalse(d)

        self.neo4j.save_safe_token_and_complete(self.gid, "SplitPledge2", "ABCDEFG", "Bob")
        d = self.neo4j.check_fan_in_complete(self.gid, "HardcopyDiscardPledge")
        self.assertTrue(d)

        self.log.info("Conditional fan-out")

        # test conditional fan-out
        d = self.neo4j.check_fan_in_complete(self.gid, "WorkstationSecurityProtocols")
        self.log.info(f"Fan-in of WorkstationSecurityProtocols completed is {d}")
        self.assertFalse(d)

        # test conditional fan-out false and true
        self.neo4j.save_safe_token_and_complete(self.gid, "ServerOrWorkstation", "ABCDEFG", "Bob")
        self.neo4j.update_node_property(self.gid, "ServerOrWorkstation", AbstractWorkflow.PARAMETER_VALUE_FIELD, "Server")
        d = self.neo4j.check_fan_in_complete(self.gid, "WorkstationSecurityProtocols")
        self.log.info(f"Fan-in of WorkstationSecurityProtocols completed is now {d}")
        self.assertTrue(d)

    def test_recursive_traversal_server(self):
        self.log.info("Testing recursive traversal (with validation; server branch)")

        # localLog = self.log
        localLog = None

        try:
            self.neo4j.validate_workflow(self.gid)
        except WorkflowError as wexc:
            self.log.error(wexc)
            self.assertTrue(False)

        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "ServerOrWorkstation" in nextSet and
            "NoBackupPledge" in nextSet and
            "TemporaryFilesPeriodicRemovalPledge" in nextSet and
            "NoCopiesPledge" in nextSet)
        self.assertTrue(len(nextSet) == 6)

        # make selection on ServerOrWorkstation and mark completed
        #self.neo4j.update_node_property(self.gid, "ServerOrWorkstation", AbstractWorkflow.PARAMETER_VALUE_FIELD, "Server")
        self.neo4j.make_conditional_selection_and_disable_branches(self.gid, "ServerOrWorkstation", "Server")
        self.neo4j.save_complete(self.gid, "ServerOrWorkstation", "Bob")
        # traverse angain for PI
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"New list of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "NoBackupPledge" in nextSet and
            "TemporaryFilesPeriodicRemovalPledge" in nextSet and
            "NoCopiesPledge" in nextSet)
        self.assertTrue(len(nextSet) == 5)

        # traverse for INP
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Alice", AbstractWorkflow.ROLE_INP,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of INP nodes {nextSet}")
        self.assertTrue("ServerUsedInOtherProjects" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # traverse for STAFF (template-user-set)
        # mark TemporaryFilesPeriodicRemovalPledge done
        self.neo4j.save_safe_token_and_complete(self.gid, "TemporaryFilesPeriodicRemovalPledge", "ABCDEFG", "Janice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Janice", AbstractWorkflow.ROLE_STAFF,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue("RestrictAccessPledge-Janice" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # mark restricted access done, try again
        self.neo4j.save_safe_token_and_complete(self.gid, "RestrictAccessPledge-Janice", "ABCDEFGH", "Janice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Janice", AbstractWorkflow.ROLE_STAFF,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue("NoIdentificationPledge-Janice" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # try different staff
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Meredith", AbstractWorkflow.ROLE_STAFF,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue("RestrictAccessPledge-Meredith" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # mark no identification done
        self.neo4j.save_safe_token_and_complete(self.gid, "NoIdentificationPledge-Janice", "ABCDEFGH", "Janice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Janice", AbstractWorkflow.ROLE_STAFF,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue("BreachReportingPledge-Janice" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # mark no breach reporting and check STAFF (should be nothing left)
        self.neo4j.save_safe_token_and_complete(self.gid, "BreachReportingPledge-Janice", "ABCDEFGH", "Janice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Janice", AbstractWorkflow.ROLE_STAFF,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue(len(nextSet) == 0)

        # now check PI again
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "NoBackupPledge" in nextSet and
            "RestrictAccessPledge-Bob" in nextSet and
            "NoCopiesPledge" in nextSet)
        self.assertTrue(len(nextSet) == 5)

        # mark PI's template-user-set nodes completed
        self.neo4j.save_safe_token_and_complete(self.gid, "RestrictAccessPledge-Bob", "ABCDEFGH", "Bob")
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.neo4j.save_safe_token_and_complete(self.gid, "NoIdentificationPledge-Bob", "ABCDEFGH", "Bob")
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.neo4j.save_safe_token_and_complete(self.gid, "BreachReportingPledge-Bob", "ABCDEFGH", "Bob")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "NoBackupPledge" in nextSet and
            "NoCopiesPledge" in nextSet)
        self.assertTrue(len(nextSet) == 4)

        # test split user-set nodes
        self.neo4j.save_safe_token_and_complete(self.gid, "NoBackupPledge", "ABCDEFGH", "Bob")
        # CodedBackupSelectionPledge should be among the next
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertFalse("CodedBackupSelectionPledge" in nextSet)

        # mark more done
        self.neo4j.save_safe_token_and_complete(self.gid, "CodeBackupSelectionPledge", "ABCDEFGH", "Bob")
        self.neo4j.save_safe_token_and_complete(self.gid, "NoCopiesPledge", "ABCDEFGH", "Bob")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "PrintEnvironment" in nextSet)
        self.assertTrue(len(nextSet) == 3)

        # try conditional fan out
        self.neo4j.save_safe_token_and_complete(self.gid, "ServerUsedInOtherProjects", "ABCDEFG", "Alice")
        self.neo4j.save_safe_token_and_complete(self.gid, "ServerSecurityProtocols", "ABCDEFG", "Alice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Alice", AbstractWorkflow.ROLE_INP,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of INP nodes {nextSet}")
        self.assertTrue("WorkstationSecurityProtocols" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # reach stop for INP
        self.neo4j.save_safe_token_and_complete(self.gid, "WorkstationSecurityProtocols", "ABCDEFG", "Alice")
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Alice", AbstractWorkflow.ROLE_INP,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of INP nodes {nextSet}")
        self.assertTrue(len(nextSet) == 0)

        # test for completeness
        d = self.neo4j.is_workflow_complete("Bob", AbstractWorkflow.ROLE_PI, self.gid)
        self.assertFalse(d)

        # get a list of incomplete common-set nodes
        d = self.neo4j.list_not_completed_common_set(self.gid)
        self.log.info(f"Incomplete common set nodes are {d}")
        self.assertTrue(len(d) == 9)

        # mark all common-set nodes listed done
        self.log.info("Marking common-set nodes {d} completed")
        for cs in d:
            self.neo4j.save_safe_token_and_complete(self.gid, cs, "ABCDEFGHJ", "Bob")

        # get a list again
        d = self.neo4j.list_not_completed_common_set(self.gid)
        self.log.info(f"Incomplete common set nodes are {d}")
        self.assertTrue(len(d) == 0)

        # traverse graph for Bob, see what is left
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of Bob the PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 1)

        # mark the userSet nodes done
        self.log.info(f"Marking user-set nodes {nextSet} completed")
        for us in nextSet:
            self.neo4j.save_safe_token_and_complete(self.gid, us, "ABCDEFGHJ", "Bob")

        # traverse graph for Bob, see what is left
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of Bob the PI nodes {nextSet}")

        d = self.neo4j.list_not_completed_common_set(self.gid)
        self.log.info(f"Incomplete common set nodes are {d}")

        self.log.info("Testing if workflow is complete")

        self.assertTrue(self.neo4j.is_workflow_complete("Bob", AbstractWorkflow.ROLE_PI, self.gid))

    def test_recursive_traversal_workstation(self):
        self.log.info("Testing recursive traversal (with validation; workstation branch) ")

        #localLog = self.log
        localLog = None

        try:
            self.neo4j.validate_workflow(self.gid)
        except WorkflowError as wexc:
            self.log.error(wexc)
            self.assertTrue(False)

        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "ServerOrWorkstation" in nextSet and
            "NoBackupPledge" in nextSet and
            "TemporaryFilesPeriodicRemovalPledge" in nextSet and
            "NoCopiesPledge" in nextSet)
        self.assertTrue(len(nextSet) == 6)

        # make selection on ServerOrWorkstation and mark completed
        #self.neo4j.update_node_property(self.gid, "ServerOrWorkstation", AbstractWorkflow.PARAMETER_VALUE_FIELD,
        #                                "Workstation")
        self.neo4j.make_conditional_selection_and_disable_branches(self.gid, "ServerOrWorkstation", "Workstation")
        self.neo4j.save_complete(self.gid, "ServerOrWorkstation", "Bob")
        # traverse again for PI
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"New list of PI nodes {nextSet}")
        self.assertTrue("IRBSubmitted" in nextSet and
            "PaymentMade" in nextSet and
            "NoBackupPledge" in nextSet and
            "TemporaryFilesPeriodicRemovalPledge" in nextSet and
            "NoCopiesPledge" in nextSet and
            "WorkstationTrainingPledge-Bob" in nextSet)
        self.assertTrue(len(nextSet) == 6)

        # traverse for INP
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Alice", AbstractWorkflow.ROLE_INP,
            self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of INP nodes {nextSet}")
        self.assertTrue("WorkstationSecurityProtocols" in nextSet)
        self.assertTrue(len(nextSet) == 1)

        # fill out network security protocols
        self.neo4j.save_safe_token_and_complete(self.gid, "WorkstationSecurityProtocols", "ABCDEFGH", "Alice")

        # reach stop for INP
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Alice", AbstractWorkflow.ROLE_INP,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of INP nodes {nextSet}")
        self.assertTrue(len(nextSet) == 0)

        # fill out PI nodes for Bob the PI
        self.neo4j.save_complete(self.gid, "IRBSubmitted", "Bob")
        self.neo4j.save_complete(self.gid, "TemporaryFilesPeriodicRemovalPledge", "Bob")
        self.neo4j.save_complete(self.gid, "NoBackupPledge", "Bob")
        self.neo4j.save_complete(self.gid, "NoCopiesPledge", "Bob")
        self.neo4j.save_complete(self.gid, "PaymentMade", "Bob")

        # check whas is next for PI
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 3)

        # fill out STAFF nodes for Bob the PI
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Janice", AbstractWorkflow.ROLE_STAFF,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of STAFF nodes {nextSet}")
        self.assertTrue(len(nextSet) == 5)
        self.log.info("Fill out those nodes for STAFF")
        for sn in nextSet:
            self.neo4j.save_complete(self.gid, sn, "Janice")

        # fill out DP nodes
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Mel", AbstractWorkflow.ROLE_DP,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of DP nodes {nextSet}")
        self.assertTrue(len(nextSet) == 1)
        for sn in nextSet:
            self.neo4j.save_complete(self.gid, sn, "Mel")

        # fill out IG nodes
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Malcolm", AbstractWorkflow.ROLE_IG,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of IG nodes {nextSet}")
        self.assertTrue(len(nextSet) == 1)
        self.neo4j.save_complete(self.gid, "IRBReceived", "Malcolm")
        self.neo4j.save_complete(self.gid, "IRBApproved", "Malcolm")
        # should be done with IG now

        # check what is next for PI and fill them out
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 3)
        self.log.info(f"Fill those nodes out")
        for sn in nextSet:
            self.neo4j.save_safe_token_and_complete(self.gid, sn, "ABCDEFG", "Bob")

        # check what is next for PI and fill them out
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 2)
        self.log.info(f"Fill those nodes out")
        for sn in nextSet:
            self.neo4j.save_safe_token_and_complete(self.gid, sn, "ABCDEFG", "Bob")

        # check what is next for PI and fill them out
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 3)
        self.log.info(f"Fill those nodes out")
        for sn in nextSet:
            self.neo4j.save_safe_token_and_complete(self.gid, sn, "ABCDEFG", "Bob")

        # check what is next for PI and fill them out
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_PI,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 1)
        self.log.info(f"Fill those nodes out")
        for sn in nextSet:
            self.neo4j.save_safe_token_and_complete(self.gid, sn, "ABCDEFG", "Bob")


        # check what is next for PI and fill them out
        nextSet = set()
        self.neo4j.find_reachable_not_completed_nodes("Bob", AbstractWorkflow.ROLE_INP,
                                                      self.gid, "Start", nextSet, localLog)
        self.log.info(f"List of PI nodes {nextSet}")
        self.assertTrue(len(nextSet) == 0)


        # verify completeness for PI
        self.assertTrue(self.neo4j.is_workflow_complete("Bob", AbstractWorkflow.ROLE_PI, self.gid, localLog))

if __name__ == '__main__':
    unittest.main()
