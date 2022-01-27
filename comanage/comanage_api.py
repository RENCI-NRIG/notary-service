import datetime
import os
import uuid

from comanage import api, logger
from nsmessages.nsmessages import send_welcome_message
from projects.models import Project
from users.models import ComanageCou, NotaryServiceUser, Affiliation, Role


# create co cou
def create_project_co_cous(project_uuid: str, project_name: str) -> bool:
    """
    Create new COmanage COUs for project membership
        - UUID-ADMIN
        - UUID-PI
        - UUID-STAFF
    """
    response = False
    for cou_flag in [os.getenv('COU_FLAG_PI_ADMIN'), os.getenv('COU_FLAG_PI_MEMBER'), os.getenv('COU_FLAG_STAFF')]:
        cou_name = str(project_uuid) + cou_flag
        cou_desc = project_name
        new_co_cou = api.cous_add(name=cou_name, description=cou_desc, parent_id=os.getenv('COU_ID_PROJECTS'))
        if new_co_cou:
            co_cou_id = new_co_cou.get('Id')
            co_cou = api.cous_view_one(cou_id=co_cou_id).get('Cous', [])
            if co_cou:
                add_co_cou(co_cou=co_cou[0])
                if cou_flag == os.getenv('COU_FLAG_STAFF'):
                    response = True
        else:
            logger.error('{0} - Create COU Failed: {1}'.format(datetime.datetime.now().ctime(), cou_name))
            return False

    return response


# add co cou
def add_co_cou(co_cou: dict) -> None:
    ns_cou = ComanageCou.objects.filter(co_cou_id=int(co_cou.get('Id'))).first()
    if ns_cou:
        logger.info(
            '{0} - Found COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name, ns_cou.description))
    else:
        ns_cou = ComanageCou()
        ns_cou.name = co_cou.get('Name')
        ns_cou.description = co_cou.get('Description', '')
        ns_cou.co_cou_id = co_cou.get('Id')
        ns_cou.co_cou_parent_id = co_cou.get('ParentId', None)
        ns_cou.save()
        logger.info(
            '{0} - Add COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name, ns_cou.description))


# remove co cou
def remove_co_cou(ns_cou: ComanageCou) -> bool:
    response = False
    rm_co_cou = api.cous_delete(cou_id=ns_cou.co_cou_id)
    if rm_co_cou:
        logger.info(
            '{0} - Remove COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name, ns_cou.description))
        ns_cou.delete()
        response = True
    else:
        logger.error(
            '{0} - Failed to remove COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name,
                                                           ns_cou.description))

    return response


# verify ns cou
def verify_ns_cou(ns_cou: ComanageCou) -> None:
    co_cou = api.cous_view_one(cou_id=ns_cou.co_cou_id).get('Cous', [])
    if co_cou:
        logger.info(
            '{0} - Found COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name, ns_cou.description))
    else:
        logger.info(
            '{0} - Remove COU: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_cou.name, ns_cou.description))
        ns_cou.delete()


# add co user
def add_co_user(co_person: dict) -> None:
    co_person_id = co_person.get('Id')
    ns_person = NotaryServiceUser.objects.filter(co_person_id=int(co_person.get('Id'))).first()
    if ns_person:
        logger.info(
            '{0} - Found CoPerson: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.name, ns_person.email))
    else:
        co_names = api.names_view_per_person(person_type='copersonid', person_id=co_person_id).get('Names', [])
        username = ''
        first_name = ''
        last_name = ''
        name = ''
        email = ''
        eppn = ''
        impactid = ''
        oidcsub = ''
        for co_name in co_names:
            if co_name.get('PrimaryName', False):
                first_name = co_name.get('Given', '')
                last_name = co_name.get('Family', '')
                name = first_name + ' ' + last_name
                break
        co_identifiers = api.identifiers_view_per_entity(entity_type='copersonid', entity_id=co_person_id).get(
            'Identifiers')
        for identifier in co_identifiers:
            if identifier.get('Type', None) == 'oidcsub':
                oidcsub = identifier.get('Identifier', '')
            if identifier.get('Type', None) == 'impactid':
                impactid = identifier.get('Identifier', '')
            if identifier.get('Type', None) == 'eppn':
                eppn = identifier.get('Identifier', '')
        co_email = api.email_addresses_view_per_person(person_type='copersonid', person_id=co_person_id).get(
                'EmailAddresses')
        for e in co_email:
            if e.get('Type', None) == 'official':
                email = e.get('Mail', '')
                username = email
                break
        kwargs = {
            'username': username,
            'first_name': first_name,
            'last_name': last_name,
            'name': name,
            'email': email
        }
        ns_person = NotaryServiceUser.objects.create_user(**kwargs)
        ns_person.display_name = '{0} ({1})'.format(ns_person.name, ns_person.email)
        ns_person.co_person_id = int(co_person.get('Id'))
        ns_person.eppn = eppn
        ns_person.co_oidc_sub = oidcsub
        ns_person.save()
        send_welcome_message(user=ns_person)
        logger.info(
            '{0} - Add CoPerson: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.name, ns_person.email))


# verify ns user
def verify_ns_user(ns_person: NotaryServiceUser) -> None:
    co_person = api.copeople_view_one(coperson_id=ns_person.co_person_id).get('CoPeople', [])
    if co_person:
        logger.info(
            '{0} - Found CoPerson: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.name, ns_person.email))
    else:
        logger.info(
            '{0} - Remove CoPerson: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.name, ns_person.email))
        ns_person.is_active = False
        ns_person.save()


# add co affiliation
def add_co_affiliation(co_person: dict) -> None:
    co_person_id = co_person.get('Id')
    ns_affiliation = Affiliation.objects.filter(co_person_id=co_person_id).first()
    if ns_affiliation:
        logger.info(
            '{0} - Found Affiliation: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_affiliation.name,
                                                        ns_affiliation.co_affiliation_id))
    else:
        org_id_link = api.coorg_identity_links_view_by_identity(
            identity_type='copersonid', identity_id=co_person_id).get('CoOrgIdentityLinks', [])
        if org_id_link:
            org_id = org_id_link[0].get('OrgIdentityId')
            org = api.org_identities_view_one(org_identity_id=org_id).get('OrgIdentities')
            ns_affiliation = Affiliation()
            ns_affiliation.co_affiliation_id = org_id
            ns_affiliation.co_person_id = co_person_id
            ns_affiliation.name = org[0].get('O')
            ns_affiliation.save()
            ns_person = NotaryServiceUser.objects.filter(co_person_id=co_person_id).first()
            ns_person.affiliation = ns_affiliation
            ns_person.save()
            logger.info(
                '{0} - Add Affiliation: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_affiliation.name,
                                                          ns_affiliation.co_affiliation_id))
    if not ns_affiliation.uuid:
        found_uuid = Affiliation.objects.filter(name=ns_affiliation.name).order_by('id').first().uuid
        if found_uuid:
            ns_affiliation.uuid = found_uuid
        else:
            ns_affiliation.uuid = uuid.uuid4()
        ns_affiliation.save()


# verify ns affiliation
def verify_ns_affiliation(ns_person: NotaryServiceUser) -> None:
    if ns_person.affiliation:
        co_affiliation = api.org_identities_view_one(
            org_identity_id=ns_person.affiliation.co_affiliation_id).get('OrgIdentities', [])
        if co_affiliation:
            logger.info(
                '{0} - Found Affiliation: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.affiliation.name,
                                                            ns_person.affiliation.co_affiliation_id))
        else:
            logger.info(
                '{0} - Remove Affiliation: {1} - {2}'.format(datetime.datetime.now().ctime(),
                                                             ns_person.affiliation.name,
                                                             ns_person.affiliation.co_affiliation_id))
            ns_person.affiliation.delete()
    else:
        logger.info(
            '{0} - Unknown Affiliation: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_person.affiliation.name,
                                                          ns_person.affiliation.co_affiliation_id))


# create co role for ns user
def create_co_person_role(co_person_id: int, co_cou_id: int) -> bool:
    response = False
    new_co_person_role = api.coperson_roles_add(coperson_id=co_person_id, cou_id=co_cou_id)
    if new_co_person_role:
        co_role_id = new_co_person_role.get('Id')
        ns_person = NotaryServiceUser.objects.filter(co_person_id=co_person_id).first()
        ns_role = Role()
        ns_role.co_role_id = co_role_id
        ns_role.co_person_id = co_person_id
        ns_role.co_cou = ComanageCou.objects.filter(co_cou_id=co_cou_id).first()
        ns_role.save()
        ns_person.roles.add(ns_role)
        ns_person.save()
        logger.info(
            '{0} - Add CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                       ns_role.co_role_id))
        response = True
    else:
        logger.info(
            '{0} - Failed to add CoPersonRole - CoPersonId: {1}'.format(datetime.datetime.now().ctime(), co_person_id))

    return response


# remove co role for ns user
def remove_co_person_role(co_person_id: int, co_cou_id: int) -> bool:
    response = False
    ns_role = Role.objects.filter(co_person_id=co_person_id, co_cou__co_cou_id=co_cou_id).first()
    co_role_removed = api.coperson_roles_delete(ns_role.co_role_id)
    if co_role_removed:
        logger.info(
            '{0} - Remove CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(),
                                                          ns_role.co_cou.name,
                                                          ns_role.co_role_id))
        ns_role.delete()
        response = True
    else:
        logger.warning(
            '{0} - Failed to remove CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(),
                                                                    ns_role.co_cou.name,
                                                                    ns_role.co_role_id))

    return response


# add co roles
def add_co_person_roles(co_person: dict) -> None:
    co_person_id = co_person.get('Id')
    co_roles = api.coperson_roles_view_per_coperson(coperson_id=co_person_id).get('CoPersonRoles', [])
    ns_person = NotaryServiceUser.objects.filter(co_person_id=co_person_id).first()
    if co_roles and ns_person:
        for co_role in co_roles:
            co_role_id = co_role.get('Id')
            ns_role = Role.objects.filter(co_role_id=co_role_id).first()
            if ns_role:
                logger.info(
                    '{0} - Found CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                                 ns_role.co_role_id))
            else:
                co_cou_id = co_role.get('CouId', None)
                if co_cou_id:
                    ns_role = Role()
                    ns_role.co_role_id = co_role_id
                    ns_role.co_person_id = co_person_id
                    ns_role.co_cou = ComanageCou.objects.filter(co_cou_id=co_cou_id).first()
                    ns_role.save()
                    ns_person.roles.add(ns_role)
                    ns_person.save()
                    logger.info(
                        '{0} - Add CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                                   ns_role.co_role_id))
                else:
                    logger.warning(
                        '{0} - Missing CouId: CoPersonRole - {1}'.format(datetime.datetime.now().ctime(), co_role_id))


# verify ns roles
def verify_ns_person_roles(ns_person: NotaryServiceUser) -> None:
    for ns_role in ns_person.roles.all():
        co_role = api.coperson_roles_view_one(coperson_role_id=ns_role.co_role_id).get('CoPersonRoles', [])
        if co_role:
            if not co_role[0].get('Deleted'):
                logger.info(
                    '{0} - Found CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                                 ns_role.co_role_id))
            else:
                logger.info(
                    '{0} - Remove CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                                  ns_role.co_role_id))
                ns_role.delete()
        else:
            logger.info(
                '{0} - Remove CoPersonRole: {1} - {2}'.format(datetime.datetime.now().ctime(), ns_role.co_cou.name,
                                                              ns_role.co_role_id))
            ns_role.delete()


# add project
def add_co_project(project_uuid: str) -> None:
    """
    Run after CoPeople, COUs and CoPersonRoles have been updated
    """
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    if ns_project:
        logger.info(
            '{0} - Found Project: UUID = {1}'.format(datetime.datetime.now().ctime(), project_uuid))
    else:
        logger.info(
            '{0} - Add Project: UUID = {1}'.format(datetime.datetime.now().ctime(), project_uuid))
        co_cou = ComanageCou.objects.filter(name=project_uuid + os.getenv('COU_FLAG_PI_ADMIN')).first()
        # create project
        ns_project = Project()
        ns_project.uuid = uuid.UUID(project_uuid)
        ns_project.name = co_cou.description
        ns_project.description = co_cou.description + ' (description autogenerated by initialization script)'
        ns_project.is_public = False
        ns_project.save()
        # add pi_admins
        pi_admins = NotaryServiceUser.objects.filter(
            roles__co_cou__name=project_uuid + os.getenv('COU_FLAG_PI_ADMIN')).all()
        if pi_admins:
            for pi_admin in pi_admins:
                logger.info(
                    '{0} - Add ADMIN User: {1}'.format(datetime.datetime.now().ctime(), pi_admin.display_name))
                ns_project.comanage_pi_admins.add(pi_admin)
                if not ns_project.created_by:
                    ns_project.created_by = pi_admin.email
            ns_project.save()
        # add pi_members
        pi_members = NotaryServiceUser.objects.filter(
            roles__co_cou__name=project_uuid + os.getenv('COU_FLAG_PI_MEMBER')).all()
        if pi_members:
            for pi_member in pi_members:
                logger.info(
                    '{0} - Add PI User: {1}'.format(datetime.datetime.now().ctime(), pi_member.display_name))
                ns_project.comanage_pi_members.add(pi_member)
            ns_project.save()
        # add staff
        staff = NotaryServiceUser.objects.filter(
            roles__co_cou__name=project_uuid + os.getenv('COU_FLAG_STAFF')).all()
        if staff:
            for s in staff:
                logger.info(
                    '{0} - Add STAFF User: {1}'.format(datetime.datetime.now().ctime(), s.display_name))
                ns_project.comanage_staff.add(s)
            ns_project.save()


# verify project
def verify_ns_project(ns_project: Project) -> None:
    """
    Run after CoPeople, COUs and CoPersonRoles have been updated
    """
    if ns_project:
        logger.info(
            '{0} - Found Project: UUID = {1}'.format(datetime.datetime.now().ctime(), ns_project.uuid))
        for cou_type in [os.getenv('COU_FLAG_PI_ADMIN'), os.getenv('COU_FLAG_PI_MEMBER'), os.getenv('COU_FLAG_STAFF')]:
            ns_cou = ComanageCou.objects.filter(name=str(ns_project.uuid) + cou_type).first()
            verify_ns_cou(ns_cou)
        for pi_admin in ns_project.comanage_pi_admins.all():
            verify_ns_user(pi_admin)
            verify_ns_person_roles(pi_admin)
            verify_ns_affiliation(pi_admin)
        for pi_member in ns_project.comanage_pi_members.all():
            verify_ns_user(pi_member)
            verify_ns_person_roles(pi_member)
            verify_ns_affiliation(pi_member)
        for staff in ns_project.comanage_staff.all():
            verify_ns_user(staff)
            verify_ns_person_roles(staff)
            verify_ns_affiliation(staff)
    else:
        logger.info(
            '{0} - Remove Project: UUID = {1}'.format(datetime.datetime.now().ctime(), ns_project.uuid))
        ns_project.delete()
