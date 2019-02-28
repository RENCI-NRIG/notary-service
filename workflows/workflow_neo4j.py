import os

from ns_workflow import Neo4jWorkflow
from neo4j import GraphDatabase, basic_auth

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


def get_neo4j_workflow_by_uuid(workflow_uuid):
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + "' RETURN path"
    results = db.run(statement).graph()
    db.close()
    nodes = []
    for node in results.nodes:
        entry = {}
        entry['id'] = node.id
        properties = {}
        entry['description'] = ''
        for key in node.keys():
            properties[key] = node[key]
            if key == 'description':
                entry['description'] = properties['description']
        entry['type'] = properties['Type']
        entry['label'] = properties['label']
        entry['properties'] = properties
        nodes.append(entry)
        if node.labels:
            entry['labels'] = node.labels
        else:
            entry['labels'] = []
    links = []
    for relationship in results.relationships:
        entry = {}
        entry['id'] = relationship.id
        entry['start_node'] = relationship.start_node.id
        entry['end_node'] = relationship.end_node.id
        entry['source'] = relationship.start_node.id
        entry['target'] = relationship.end_node.id
        properties = {}
        for key in relationship.keys():
            properties[key] = relationship[key]
        entry['properties'] = properties
        entry['type'] = relationship.type
        links.append(entry)
    graph = {'nodes': nodes, 'links': links}
    return graph
