import os
from time import time

from dotenv import load_dotenv
from neo4j import GraphDatabase
from ns_workflow import Neo4jWorkflow

load_dotenv('env.python')

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')

neo4j = Neo4jWorkflow(
    url=bolt_url,
    user=neo_user,
    pswd=neo_pass,
    importDir=import_dir,
    importHostDir=import_host_dir
)


def create_graph_from_file(graphml_file, graph_uuid):
    with open(graphml_file, 'r') as graphmlFile:
        graphml = graphmlFile.read()
    tc_0 = time()
    gid = neo4j.import_workflow(graphml=graphml, graphId=str(graph_uuid))
    tc_1 = time()
    is_valid = False
    tv_0 = 0
    tv_1 = 0
    if gid == str(graph_uuid):
        tv_0 = time()
        is_valid = neo4j.validate_workflow(str(graph_uuid))
        tv_1 = time()
    return graph_uuid, is_valid, (tc_1 - tc_0), (tv_1 - tv_0)


def is_workflow_complete(graph_uuid):
    tc_0 = time()
    is_complete = neo4j.is_workflow_complete(principalId='metrics', role='PI', graphId=str(graph_uuid))
    tc_1 = time()
    return graph_uuid, is_complete, (tc_1 - tc_0)


def set_workflow_nodes_as_completed(graph_uuid):
    driver = GraphDatabase.driver(bolt_url, auth=(neo_user, neo_pass))
    query = "MATCH (n) WHERE n.GraphID = '" + graph_uuid + "' AND NOT (n.Type = 'Start' OR n.Type = 'Stop') SET n.completed='True' return (n)"
    with driver.session() as session:
        val = session.run(query)


def delete_workflow_by_uuid(graph_uuid):
    neo4j.delete_workflow(str(graph_uuid))


def delete_all_nodes():
    driver = GraphDatabase.driver(bolt_url, auth=(neo_user, neo_pass))
    query = "MATCH(n) DETACH DELETE n;"
    with driver.session() as session:
        val = session.run(query)
