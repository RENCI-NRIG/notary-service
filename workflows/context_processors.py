import os
from urllib.parse import urlparse


def export_neo4j_vars(request):
    data = {}
    data['neo4j_bolt_url'] = os.getenv('NEO4J_BOLT_URL')
    data['neo4j_user'] = os.getenv('NEO4J_USER')
    data['neo4j_pass'] = os.getenv('NEO4J_PASS')
    bolt_domain = urlparse(os.getenv('NEO4J_BOLT_URL'))
    neo4j_http = 'http://' + bolt_domain.hostname + ':7474/browser'
    neo4j_https = 'https://' + bolt_domain.hostname + ':7473/browser'
    data['neo4j_http'] = neo4j_http
    data['neo4j_https'] = neo4j_https
    return data
