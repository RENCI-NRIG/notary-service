import os

from neo4j import GraphDatabase, basic_auth
from ns_workflow import Neo4jWorkflow

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


def convert_comanage_role_id_to_neo4j_node_role(role_id):
    """
    converts role_id to string based on Role model (from users)
    :param role_id:
    :return:
    """
    index = int(role_id) - 1
    ROLE_CHOICES = [
        'NSADMIN',
        'STAFF',
        'DP',
        'INP',
        'IG',
        'PI',
        'PI',
        'NO_ROLE'
    ]
    return str(ROLE_CHOICES[index])


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
    gid = neo4j.import_workflow(graphml=graphml, graphId=str(workflow_uuid))
    if gid == str(workflow_uuid):
        return True
    else:
        return False


def delete_workflow_by_uuid(workflow_uuid):
    neo4j = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importDir=import_dir,
        importHostDir=import_host_dir
    )
    neo4j.delete_workflow(str(workflow_uuid))


def get_neo4j_workflow_by_uuid(workflow_uuid):
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + \
                "' AND n.SAFEType in ['common-set', 'template-user-set', 'None'] RETURN path"
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
            if key == 'Role':
                entry['description'] += str('Role: ' + properties['Role'] + '\n')
            if key == 'description':
                entry['description'] += str('Description: ' + properties['description'] + '\n')
            if key == 'SAFEType':
                entry['safetype'] = properties['SAFEType']
        entry['description'] = entry['description'].rstrip('\n')
        entry['type'] = properties['Type']
        entry['label'] = properties['label']
        entry['properties'] = properties
        nodes.append(entry)
        if node.labels:
            # TODO: figure out why "frozenset({'Node'})" is returned for node.labels
            # entry['labels'] = node.labels
            entry['labels'] = []
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


def get_neo4j_workflow_by_uuid_and_role(workflow_uuid, role_id, user_dn):
    # from pprint import pprint
    role = convert_comanage_role_id_to_neo4j_node_role(role_id)
    bolt_driver = GraphDatabase.driver(bolt_url, auth=basic_auth(neo_user, neo_pass))
    db = bolt_driver.session()
    statement = "MATCH path = (n)-[r]->(m) WHERE n.GraphID = '" + str(workflow_uuid) + \
                "' AND n.SAFEType in ['common-set', 'template-user-set', 'None', 'user-set'] RETURN path"
    results = db.run(statement).graph()
    db.close()
    nodes = []
    for node in results.nodes:
        roles = ''
        entry = {}
        entry['id'] = node.id
        properties = {}
        entry['description'] = ''
        for key in node.keys():
            properties[key] = node[key]
            if key == 'Role':
                entry['description'] += str('Role: ' + properties['Role'] + '\n')
                roles = properties['Role']
            if key == 'description':
                entry['description'] += str('Description: ' + properties['description'] + '\n')
            if key == 'SAFEType':
                entry['safetype'] = properties['SAFEType']
            if key == 'principal':
                entry['principal'] = properties['principal']
        entry['description'] = entry['description'].rstrip('\n')
        entry['type'] = properties['Type']
        entry['label'] = properties['label']
        entry['properties'] = properties
        if role in roles or entry['type'] in 'Start,Stop':
            entry['path'] = 'True'
            if node['completed'] == 'True':
                entry['completed'] = 'True'
        else:
            entry['path'] = 'False'
        if entry['safetype'] == 'user-set':
            if entry['principal'] == str(user_dn):
                nodes.append(entry)
        else:
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
    # pprint(graph)
    return graph
