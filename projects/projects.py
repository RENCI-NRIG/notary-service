import os

from ldap3 import Connection, Server, ALL
from .models import ComanageGroup

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def get_ldap_comanage_groups():
    ldap_search_filter = '(&(objectClass=groupOfNames)(cn=CO:COU:*))'
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    groups_found = conn.search(
        ldap_search_base,
        ldap_search_filter,
        attributes=['cn']
    )
    if groups_found:
        attributes = conn.entries
    else:
        attributes = []
    conn.unbind()
    return attributes


def update_comanage_group():
    group_list = get_ldap_comanage_groups()
    ComanageGroup.objects.update(active=False)
    for group in group_list:
        dn = str(group.entry_dn)
        cn = str(group.cn[0])
        if not ComanageGroup.objects.filter(dn=dn).exists():
            ComanageGroup.objects.create(dn=dn, cn=cn, active=True)
        else:
            ComanageGroup.objects.filter(dn=dn, cn=cn).update(active=True)
