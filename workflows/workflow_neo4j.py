import os

from ns_workflow import Neo4jWorkflow

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


def create_workflow_from_template(graphml_file, workflow_uuid):
    graphmlFile = open('./media/' + graphml_file, "r")
    graphml = graphmlFile.read()
    graphmlFile.close()
    neo4j = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importDir=import_dir,
        importHostDir=import_host_dir
    )
    gid = neo4j.import_workflow(graphml=graphml, graphId=workflow_uuid)
    if gid == workflow_uuid:
        return True
    else:
        return False


def delete_workflow_from_uuid(workflow_uuid):
    neo4j = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importDir=import_dir,
        importHostDir=import_host_dir
    )
    neo4j.delete_workflow(workflow_uuid)
