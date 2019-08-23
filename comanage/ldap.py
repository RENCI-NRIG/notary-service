import os
import re

from ldap3 import Connection, Server, ALL

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def get_comanage_project_names():
    ldap_search_filter = '(objectclass=groupOfNames)'
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    personnel_found = conn.search(
        ldap_search_base,
        ldap_search_filter,
        attributes='cn'
    )
    comanage_output = ''
    if personnel_found:
        for entry in conn.entries:
            comanage_output = comanage_output + str(entry)
    conn.unbind()
    comanage_projects = re.findall(r'\B\s*cn:\s{1}[COU?:]+(\w+)-PI:admins', comanage_output)
    # print(comanage_projects)
    return comanage_projects


def get_ldap_attributes(user):
    if user.eppn:
        ldap_search_filter = '(eduPersonPrincipalName=' + user.eppn + ')'
    else:
        ldap_search_filter = '(mail=' + user.email + ')'
    # COmanage LDAP appears inconsistent when including eduPersonPrincipalName (eppn), so using user.email only
    # ldap_search_filter = '(mail=' + user.email + ')'
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
