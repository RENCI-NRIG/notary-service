import json
import os
import re

from ldap3 import Connection, Server, ALL
from comanage.comanage_api import create_project_co_cous, create_co_person_role
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages

from users.models import Affiliation, NotaryServiceUser, ComanageCou
from .models import ComanageStaff, ComanagePIAdmin, ComanagePIMember, ComanagePersonnel, Project, \
    MembershipComanagePIAdmin, MembershipComanagePIMember, MembershipComanageStaff, \
    MembershipComanagePersonnel, MembershipAffiliations, MembershipProjectWorkflow
from .workflows import create_base_project_workflows
from comanage import api

ldap_host = os.getenv('LDAP_HOST', '')
ldap_user = os.getenv('LDAP_USER', '')
ldap_password = os.getenv('LDAP_PASSWORD', '')
ldap_search_base = os.getenv('LDAP_SEARCH_BASE', '')

server = Server(ldap_host, use_ssl=True, get_info=ALL)


def project_workflow_dataset_affiliation_check(project_obj, user):
    affiliation_list = Project.objects.values_list('affiliations__uuid', flat=True).filter(
        uuid=project_obj.uuid
    )
    ds_list = Project.objects.values_list('datasets__uuid', flat=True).filter(
        uuid=project_obj.uuid
    )
    for ds in ds_list:
        for affiliation in affiliation_list:
            if not MembershipProjectWorkflow.objects.filter(
                    project=project_obj,
                    dataset=ds,
                    affiliation=affiliation
            ).exists():
                create_base_project_workflows(project_obj.uuid, user)


def update_project_affiliations(project_obj, user):
    """
    Update affiliation based on project personnel
    :param project_obj:
    :param user:
    :return:
    """
    if user.is_pi or user.is_nsstaff:
        local_affiliations = Affiliation.objects.filter(
            uuid__in=MembershipAffiliations.objects.values_list('affiliation__uuid', flat=True).filter(
                project=project_obj
            )
        )
        # add project/affiliation relationship if it does not exist
        user_affiliation = Affiliation.objects.get(uuid=user.ns_affiliation)
        if user_affiliation not in local_affiliations:
            # print(f"Adding affiliation: {user_affiliation}")
            MembershipAffiliations.objects.create(
                project=project_obj,
                affiliation=Affiliation.objects.get(
                    uuid=user.ns_affiliation
                )
            )


def update_comanage_personnel_membership(project_obj, comanage_groups):
    """
    Update comanage personnel membership tables based on role
    :param project_obj:
    :param comanage_groups:
    :return:
    """
    # print(comanage_groups[0].cn)
    role_type = re.findall(
        re.escape(project_obj.comanage_name) + r'[-\w]*-(\w+:(?:admins|members:active))',
        str(comanage_groups[0].cn)
    )
    # get comanage group personnel
    comanage_personnel = []
    for group in comanage_groups:
        comanage_personnel += personnel_by_comanage_group(cn=group.cn)
    # get local group/project personnel
    local_personnel = []
    if role_type[0] == 'STAFF:members:active':
        local_personnel = ComanagePersonnel.objects.filter(
            id__in=list(MembershipComanagePersonnel.objects.values_list('person_id', flat=True).filter(
                project=project_obj,
                comanage_staff__isnull=False
            ))
        )
    elif role_type[0] == 'PI:members:active':
        local_personnel = ComanagePersonnel.objects.filter(
            id__in=list(MembershipComanagePersonnel.objects.values_list('person_id', flat=True).filter(
                project=project_obj,
                comanage_pi_members__isnull=False
            ))
        )
    elif role_type[0] == 'PI:admins':
        local_personnel = ComanagePersonnel.objects.filter(
            id__in=list(MembershipComanagePersonnel.objects.values_list('person_id', flat=True).filter(
                project=project_obj,
                comanage_pi_admins__isnull=False
            ))
        )

    # remove entry when local personnel not in comanage personnel
    for person in local_personnel:
        if role_type[0] == 'STAFF:members:active':
            if person not in comanage_personnel:
                MembershipComanagePersonnel.objects.filter(
                    person=person,
                    project=project_obj,
                    comanage_staff__isnull=False
                ).delete()
        elif role_type[0] == 'PI:members:active':
            if person not in comanage_personnel:
                MembershipComanagePersonnel.objects.filter(
                    person=person,
                    project=project_obj,
                    comanage_pi_members__isnull=False
                ).delete()
        elif role_type[0] == 'PI:admins':
            if person not in comanage_personnel:
                MembershipComanagePersonnel.objects.filter(
                    person=person,
                    project=project_obj,
                    comanage_pi_admins__isnull=False
                ).delete()

    # create entry when comanage personnel not in local personnel
    for group in comanage_groups:
        comanage_personnel = personnel_by_comanage_group(cn=group.cn)
        for person in comanage_personnel:
            if role_type[0] == 'STAFF:members:active':
                if not MembershipComanagePersonnel.objects.filter(
                        person=person,
                        project=project_obj,
                        comanage_staff__isnull=False
                ).exists():
                    MembershipComanagePersonnel.objects.create(
                        person=person,
                        project=project_obj,
                        comanage_pi_admins=None,
                        comanage_pi_members=None,
                        comanage_staff=ComanageStaff.objects.get(id=group.id),
                        dataset_dso=None,
                        affiliation_ig=None,
                        infrastructure_inp=None,
                    )
            elif role_type[0] == 'PI:members:active':
                if not MembershipComanagePersonnel.objects.filter(
                        person=person,
                        project=project_obj,
                        comanage_pi_members__isnull=False
                ).exists():
                    MembershipComanagePersonnel.objects.create(
                        person=person,
                        project=project_obj,
                        comanage_pi_admins=None,
                        comanage_pi_members=ComanagePIMember.objects.get(id=group.id),
                        comanage_staff=None,
                        dataset_dso=None,
                        affiliation_ig=None,
                        infrastructure_inp=None,
                    )
            elif role_type[0] == 'PI:admins':
                if not MembershipComanagePersonnel.objects.filter(
                        person=person,
                        project=project_obj,
                        comanage_pi_admins__isnull=False
                ).exists():
                    MembershipComanagePersonnel.objects.create(
                        person=person,
                        project=project_obj,
                        comanage_pi_admins=ComanagePIAdmin.objects.get(id=group.id),
                        comanage_pi_members=None,
                        comanage_staff=None,
                        dataset_dso=None,
                        affiliation_ig=None,
                        infrastructure_inp=None,
                    )


def update_project_staff(project_obj):
    """
    Update project / STAFF:members:active membership tables
    :param project_obj:
    :return:
    """
    # get staff from comanage
    # match form: [COU?:]+(\w+)[-\w+]*-STAFF:members:active
    cn_regex = r'[COU?:]+' + re.escape(project_obj.comanage_name) + r'[-\w+]*-STAFF:members:active'
    comanage_staff = ComanageStaff.objects.filter(
        cn__iregex=cn_regex
    )
    # get local pi members
    local_staff = ComanageStaff.objects.filter(
        cn__in=MembershipComanageStaff.objects.values_list('comanage_group__cn', flat=True).filter(
            project=project_obj
        )
    )
    # compare pi member sets
    # print('----- STAFF:members:active -----')
    # print('local: ' + str(local_staff))
    # print('comanage: ' + str(comanage_staff))
    # remove project/staff relationships that are no longer valid
    for staff in local_staff:
        if staff not in comanage_staff:
            # remove from project personnel membership
            MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                comanage_staff=ComanageStaff.objects.get(id=staff.id)
            ).delete()
            # remove from group membership
            MembershipComanageStaff.objects.filter(
                project=project_obj,
                comanage_group=staff
            ).delete()
    # create project/staff relationships if they do not yet exist
    for staff in comanage_staff:
        if not MembershipComanageStaff.objects.filter(
                project=project_obj,
                comanage_group=staff
        ).exists():
            MembershipComanageStaff.objects.create(
                project=project_obj,
                comanage_group=staff
            )

    if comanage_staff:
        update_comanage_personnel_membership(project_obj=project_obj, comanage_groups=comanage_staff)


def update_project_pi(project_obj):
    """
    Update project / PI:members:active membership tables
    :param project_obj:
    :return:
    """
    # get pi members from comanage
    # match form: [COU?:]+(\w+)[-\w+]*-PI:members:active
    cn_regex = r'[COU?:]+' + re.escape(project_obj.comanage_name) + r'[-\w+]*-PI:members:active'
    comanage_pi_member = ComanagePIMember.objects.filter(
        cn__iregex=cn_regex
    )
    # get local pi members
    local_pi_member = ComanagePIMember.objects.filter(
        cn__in=MembershipComanagePIMember.objects.values_list('comanage_group__cn', flat=True).filter(
            project=project_obj
        )
    )
    # compare pi member sets
    # print('----- PI:members:active -----')
    # print('local: ' + str(local_pi_member))
    # print('comanage: ' + str(comanage_pi_member))
    # remove project/pi relationships that are no longer valid
    for pi_member in local_pi_member:
        if pi_member not in comanage_pi_member:
            # remove from project personnel membership
            MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                comanage_pi_members=ComanagePIMember.objects.get(id=pi_member.id)
            ).delete()
            # remove from group membership
            MembershipComanagePIMember.objects.filter(
                project=project_obj,
                comanage_group=pi_member
            ).delete()
    # create project/pi relationships if they do not yet exist
    for pi_member in comanage_pi_member:
        if not MembershipComanagePIMember.objects.filter(
                project=project_obj,
                comanage_group=pi_member
        ).exists():
            MembershipComanagePIMember.objects.create(
                project=project_obj,
                comanage_group=pi_member
            )

    if comanage_pi_member:
        update_comanage_personnel_membership(project_obj=project_obj, comanage_groups=comanage_pi_member)


def update_project_pi_admin(project_obj):
    """
    Update project / PI:admins membership tables
    :param project_obj:
    :return:
    """
    # get pi_admins from comanage
    # match form: [COU?:]+(\w+)[-\w+]*-PI:admins
    cn_regex = r'[COU?:]+' + re.escape(project_obj.comanage_name) + r'[-\w+]*-PI:admins'
    comanage_pi_admins = ComanagePIAdmin.objects.filter(
        cn__iregex=cn_regex
    )
    # get local pi_admins
    local_pi_admins = ComanagePIAdmin.objects.filter(
        cn__in=MembershipComanagePIAdmin.objects.values_list('comanage_group__cn', flat=True).filter(
            project=project_obj
        )
    )
    # compare pi_admin sets
    # print('----- PI:admins -----')
    # print('local: ' + str(local_pi_admins))
    # print('comanage: ' + str(comanage_pi_admins))
    # remove project/pi_admin relationships that are no longer valid
    for pi_admin in local_pi_admins:
        if pi_admin not in comanage_pi_admins:
            # remove from project personnel membership
            MembershipComanagePersonnel.objects.filter(
                project=project_obj,
                comanage_pi_admins=ComanagePIAdmin.objects.get(id=pi_admin.id)
            ).delete()
            # remove from group membership
            MembershipComanagePIAdmin.objects.filter(
                project=project_obj,
                comanage_group=pi_admin
            ).delete()
    # create project/pi_admin relationships if they do not yet exist
    for pi_admin in comanage_pi_admins:
        if not MembershipComanagePIAdmin.objects.filter(
                project=project_obj,
                comanage_group=pi_admin
        ).exists():
            MembershipComanagePIAdmin.objects.create(
                project=project_obj,
                comanage_group=pi_admin
            )

    if comanage_pi_admins:
        update_comanage_personnel_membership(project_obj=project_obj, comanage_groups=comanage_pi_admins)


def update_project_personnel(project_obj):
    """
    Update project personnel (PI_ADMIN, PI, STAFF)
    :param project_obj:
    :return:
    """
    update_comanage_group()
    update_comanage_personnel()
    update_project_pi_admin(project_obj=project_obj)
    update_project_pi(project_obj=project_obj)
    update_project_staff(project_obj=project_obj)
    project_obj.save()


def create_new_project(request, project_name: str, project_description: str, is_public: bool):
    project = Project()
    if create_project_co_cous(project_uuid=project.uuid, project_name=project_name):
        project.created_by = request.user.email
        project.name = project_name
        project.description = project_description
        project.is_public = is_public
        project.save()
        # add pi_admin role for created_by user
        cou_name = str(project.uuid) + os.getenv('COU_FLAG_PI_ADMIN')
        ns_cou = ComanageCou.objects.filter(name=cou_name).first()
        if create_co_person_role(co_person_id=request.user.co_person_id, co_cou_id=ns_cou.co_cou_id):
            project.comanage_pi_admins.add(request.user)
            project.save()
        else:
            messages.error(
                request,
                'ERROR! Unable to assign {0} to Project {1} ...'.format(os.getenv('COU_FLAG_PI_ADMIN'), project_name))
        return str(project.uuid)
    else:
        messages.error(request, 'ERROR! Unable to create Project {0} ...'.format(project_name))
        redirect('projects')

    # if project_name:
    #     project.name = project_name
    # else:
    #     project.name = f"Untitled ({comanage_project})"
    # if project_description:
    #     project.description = project_description
    # else:
    #     project.description = f"Untitled ({comanage_project})"
    # project.comanage_name = str(comanage_project)
    # project.save()
    # update_project_personnel(project_obj=project)
    # return str(project.uuid)


def get_ldap_comanage_staff():
    # ldap_search_filter = '(&(objectClass=groupOfNames)(cn=CO:COU:*))'
    # conn = Connection(server, ldap_user, ldap_password, auto_bind=True)
    # groups_found = conn.search(
    #     ldap_search_base,
    #     ldap_search_filter,
    #     attributes=['cn']
    # )
    # if groups_found:
    #     attributes = conn.entries
    # else:
    #     attributes = []
    # conn.unbind()
    # print('## projects.get_ldap_comanage_staff: attributes ##')
    # print('*** UPDATED ***')
    # print(attributes)
    comanage_staff = []
    co_cous = api.cous_view_per_co().get('Cous', [])
    if co_cous:
        for cou in co_cous:
            comanage_staff.append({'dn': cou.get('Description', 'DN_BLANK'), 'cn': cou.get('Name', 'CN_BLANK')})
    return comanage_staff


def update_comanage_group():
    group_list = get_ldap_comanage_staff()
    ComanagePIAdmin.objects.update(active=False)
    ComanagePIMember.objects.update(active=False)
    ComanageStaff.objects.update(active=False)
    for group in group_list:
        # dn = str(group.entry_dn)
        dn = group.get('dn')
        # cn = str(group.cn[0])
        cn = group.get('cn')
        if os.getenv('ROLE_PI_ADMIN') in cn:
            if not ComanagePIAdmin.objects.filter(dn=dn).exists():
                ComanagePIAdmin.objects.create(dn=dn, cn=cn, active=True)
            else:
                ComanagePIAdmin.objects.filter(dn=dn, cn=cn).update(active=True)
        elif os.getenv('ROLE_PI_MEMBER') in cn:
            if not ComanagePIMember.objects.filter(dn=dn).exists():
                ComanagePIMember.objects.create(dn=dn, cn=cn, active=True)
            else:
                ComanagePIMember.objects.filter(dn=dn, cn=cn).update(active=True)
        elif os.getenv('ROLE_STAFF') in cn:
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
        attributes=['cn', 'employeeNumber', 'eduPersonPrincipalName', 'mail', 'uid']
    )
    if personnel_found:
        attributes = conn.entries
    else:
        attributes = []
    conn.unbind()
    # print('## projects.get_comanage_personnel: attributes ##')
    # print(attributes)
    comanage_personnel = []
    co_people = api.copeople_view_per_co().get('CoPeople', [])
    if co_people:
        for co_person in co_people:
            co_person_id = co_person.get('Id')
            # get name
            conames = api.names_view_per_person(
                person_type='copersonid', person_id=co_person_id).get('Names')
            name = ''
            for coname in conames:
                if coname.get('PrimaryName', False):
                    family = coname.get('Family', '')
                    given = coname.get('Given', '')
                    name = given + ' ' + family
            # get email
            coemail = api.email_addresses_view_per_person(
                person_type='copersonid', person_id=co_person_id).get('EmailAddresses')
            email = ''
            for e in coemail:
                if e.get('Type', None) == 'official':
                    email = e.get('Mail', '')
                    break
            # get oidcsub, impactid, eppn
            oidcsub = ''
            impactid = ''
            eppn = ''
            coidentifiers = api.identifiers_view_per_entity(
                entity_type='copersonid', entity_id=co_person_id).get('Identifiers')
            for ident in coidentifiers:
                if ident.get('Type', None) == 'oidcsub':
                    oidcsub = ident.get('Identifier', '')
                    oidcsub_id = str(oidcsub).rsplit('/', 1)[1]
                if ident.get('Type', None) == 'impactid':
                    impactid = ident.get('Identifier', '')
                if ident.get('Type', None) == 'eppn':
                    eppn = ident.get('Identifier', '')
            comanage_personnel.append({
                'dn': co_person_id,
                'cn': name,
                'eppn': eppn,
                'employee_number': impactid,
                'email': email,
                'uid': oidcsub
            })
    # print(comanage_personnel)
    return comanage_personnel


def update_comanage_personnel():
    person_list = get_comanage_personnel()
    ComanagePersonnel.objects.update(active=False)
    for person in person_list:
        # dn = str(person.entry_dn)
        # cn = str(person.cn[0])
        # employee_number = str(person.employeeNumber[0])
        # if person.eduPersonPrincipalName:
        #     eppn = str(person.eduPersonPrincipalName[0])
        # else:
        #     eppn = ''
        # email = str(person.mail[0])
        # uid = str(person.uid[0])
        dn = person.get('dn')
        cn = person.get('cn')
        employee_number = person.get('employee_number')
        eppn = person.get('eppn')
        email = person.get('email')
        uid = person.get('uid', 'OIDC_SUB_BLANK')
        if not ComanagePersonnel.objects.filter(dn=dn).exists():
            ComanagePersonnel.objects.create(
                dn=dn,
                cn=cn,
                employee_number=employee_number,
                eppn=eppn,
                email=email,
                uid=uid,
                active=True)
        else:
            ComanagePersonnel.objects.filter(dn=dn, employee_number=employee_number).update(active=True)


def personnel_by_comanage_group(cn):
    # print(cn)
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
                attributes.append(ComanagePersonnel.objects.get(employee_number=employee_number, active=True))
    else:
        attributes = []
    conn.unbind()
    # print('## projects.personnel_by_comanage_group: attributes ##')
    # print(attributes)
    return attributes
