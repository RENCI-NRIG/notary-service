import os

from ldap3 import Connection, Server, ALL

from .models import ComanageStaff, ComanagePIAdmin, ComanagePIMember, ComanagePersonnel

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def get_ldap_comanage_staff():
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
    group_list = get_ldap_comanage_staff()
    ComanagePIAdmin.objects.update(active=False)
    ComanagePIMember.objects.update(active=False)
    ComanageStaff.objects.update(active=False)
    for group in group_list:
        dn = str(group.entry_dn)
        cn = str(group.cn[0])
        if "-PI:admins" in cn:
            if not ComanagePIAdmin.objects.filter(dn=dn).exists():
                ComanagePIAdmin.objects.create(dn=dn, cn=cn, active=True)
            else:
                ComanagePIAdmin.objects.filter(dn=dn, cn=cn).update(active=True)
        elif "-PI:members:active" in cn:
            if not ComanagePIMember.objects.filter(dn=dn).exists():
                ComanagePIMember.objects.create(dn=dn, cn=cn, active=True)
            else:
                ComanagePIMember.objects.filter(dn=dn, cn=cn).update(active=True)
        elif "-STAFF:members:active" in cn:
            if not ComanageStaff.objects.filter(dn=dn).exists():
                ComanageStaff.objects.create(dn=dn, cn=cn, active=True)
            else:
                ComanageStaff.objects.filter(dn=dn, cn=cn).update(active=True)


def get_comanage_personnel():
    ldap_search_filter = '(objectclass=person)'
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    personnel_found = conn.search(
        ldap_search_base,
        ldap_search_filter,
        attributes=['cn', 'employeeNumber', 'eduPersonPrincipalName', 'mail']
    )
    if personnel_found:
        attributes = conn.entries
    else:
        attributes = []
    conn.unbind()
    return attributes


def update_comanage_personnel():
    person_list = get_comanage_personnel()
    ComanagePersonnel.objects.update(active=False)
    for person in person_list:
        dn = str(person.entry_dn)
        cn = str(person.cn[0])
        employee_number = str(person.employeeNumber[0])
        if person.eduPersonPrincipalName:
            eppn = str(person.eduPersonPrincipalName[0])
        else:
            eppn = ''
        email = str(person.mail[0])
        if not ComanagePersonnel.objects.filter(dn=dn).exists():
            ComanagePersonnel.objects.create(
                dn=dn,
                cn=cn,
                employee_number=employee_number,
                eppn=eppn,
                email=email,
                active=True)
        else:
            ComanagePersonnel.objects.filter(dn=dn, employee_number=employee_number).update(active=True)


def personnel_by_comanage_group(cn):
    ldap_search_filter = '(&(objectClass=groupOfNames)(cn=' + cn + '))'
    conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    personnel_found = conn.search(
        ldap_search_base,
        ldap_search_filter,
        attributes=['member']
    )
    if personnel_found:
        personnel = conn.entries
        attributes = []
        for person in personnel[0]['member']:
            employee_number = person.split(',')[0].split('=')[1]
            if ComanagePersonnel.objects.filter(employee_number=employee_number).exists():
                attributes.append(ComanagePersonnel.objects.get(employee_number=employee_number))
    else:
        attributes = []
    conn.unbind()
    return attributes
