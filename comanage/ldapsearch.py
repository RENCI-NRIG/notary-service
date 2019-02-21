import os

from ldap3 import Connection, Server, ALL

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def get_ldap_attributes(user):
    if user.eppn:
        ldap_search_filter = '(eduPersonPrincipalName=' + user.eppn + ')'
    else:
        ldap_search_filter = '(mail=' + user.email + ')'
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    profile_found = conn.search(ldap_search_base,
                                ldap_search_filter,
                                attributes=[
                                    'isMemberOf',
                                    'objectClass',
                                    'employeeNumber',
                                    'uid',
                                    'eduPersonAffiliation',
                                    'eduPersonPrincipalName',
                                ])
    if profile_found:
        attributes = conn.entries[0]
    else:
        attributes = []
    conn.unbind()
    return attributes
