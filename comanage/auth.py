import unicodedata
from builtins import any

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from apache_kafka.producer import send_ns_message
from users.models import Role, Affiliation
from users.views import set_role_boolean
from .ldapsearch import get_ldap_attributes
from .models import IsMemberOf, MembershipIsMemberOf, LdapOther, MembershipLdapOther


def generate_username(email):
    return unicodedata.normalize('NFKC', email)[:150]


def check_ismemberof(attributelist):
    if attributelist['isMemberOf']:
        for attribute in attributelist['isMemberOf']:
            if not IsMemberOf.objects.filter(value=attribute).exists():
                IsMemberOf.objects.create(attribute='isMemberOf', value=attribute)


def update_membership_ismemberof(user, attributelist):
    ismeberof_new = list(attributelist['isMemberOf'])
    ismeberof_cur = list(MembershipIsMemberOf.objects.values_list('ismemberof__value').filter(
        user=user
    ))
    for cou in ismeberof_cur:
        if not any(cou[0] in x for x in ismeberof_new):
            print('Deletiing COU: ' + str(cou[0]))
            MembershipIsMemberOf.objects.filter(
                user=user,
                ismemberof__value=cou[0],
            ).delete()
    for attribute in attributelist['isMemberOf']:
        attr_id = IsMemberOf.objects.get(attribute='isMemberOf', value=attribute).pk
        if not MembershipIsMemberOf.objects.filter(user=user.id, ismemberof=attr_id).exists():
            print('Adding COU: ' + str(attribute))
            MembershipIsMemberOf.objects.create(user=user, ismemberof=IsMemberOf.objects.get(id=attr_id))


def check_ldapother_attributes(attributelist):
    if attributelist['eduPersonAffiliation']:
        for attribute in attributelist['eduPersonAffiliation']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='eduPersonAffiliation', value=attribute)
    if attributelist['eduPersonPrincipalName']:
        for attribute in attributelist['eduPersonPrincipalName']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='eduPersonPrincipalName', value=attribute)
    if attributelist['employeeNumber']:
        for attribute in attributelist['employeeNumber']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='employeeNumber', value=attribute)
    if attributelist['objectClass']:
        for attribute in attributelist['objectClass']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='objectClass', value=attribute)
    if attributelist['uid']:
        for attribute in attributelist['uid']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='uid', value=attribute)


def update_ldapother_ismemberof(user, attributelist):
    for attribute in attributelist['eduPersonAffiliation']:
        attr_id = LdapOther.objects.get(attribute='eduPersonAffiliation', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))
    for attribute in attributelist['eduPersonPrincipalName']:
        attr_id = LdapOther.objects.get(attribute='eduPersonPrincipalName', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))
    for attribute in attributelist['employeeNumber']:
        attr_id = LdapOther.objects.get(attribute='employeeNumber', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))
    for attribute in attributelist['objectClass']:
        attr_id = LdapOther.objects.get(attribute='objectClass', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))
    for attribute in attributelist['uid']:
        attr_id = LdapOther.objects.get(attribute='uid', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))


class MyOIDCAB(OIDCAuthenticationBackend):
    def set_user_roles(self, user):
        ns_roles = [
            ('NSADMIN', '-NSADMIN:admins'),
            ('STAFF', '-STAFF:members:active'),
            ('DP', '-DP:members:active'),
            ('INP', '-INP:members:active'),
            ('IG', '-IG:members:active'),
            ('PI_ADMIN', '-PI:admins'),
            ('PI_MEMBER', '-PI:members:active'),
            ('NO_ROLE', '-NOROLE'),
        ]
        ismember_list = MembershipIsMemberOf.objects.values_list(
            'ismemberof__value', flat=True
        ).filter(user=user)
        for role_pair in ns_roles:
            role = role_pair[0]
            expr = role_pair[1]
            # if role is part of user ismemberof list, add role if it does not already exist
            if any(expr in x for x in ismember_list):
                if not user.roles.filter(id=int(getattr(Role, role))).exists():
                    user.roles.add(int(getattr(Role, role)))
                    print("Adding role " + str(Role.objects.get(id=int(getattr(Role, role)))))
            else:
                if user.roles.filter(id=int(getattr(Role, role))).exists() and getattr(Role, role) != Role.NO_ROLE:
                    user.roles.remove(int(getattr(Role, role)))
                    print("Removing role " + str(Role.objects.get(id=int(getattr(Role, role)))))
        if any('-NSADMIN:admins' in x for x in ismember_list):
            user.is_staff = True
            user.is_superuser = True
        else:
            user.is_staff = False
            user.is_superuser = False
        set_role_boolean(user)

    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)
        user.first_name = claims.get('given_name', '')
        user.given_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.family_name = claims.get('family_name', '')
        user.idp = claims.get('idp', '')
        user.idp_name = claims.get('idp_name', '')
        user.sub = claims.get('sub', '')
        user.aud = claims.get('aud', '')
        user.cert_subject_dn = claims.get('cert_subject_dn', '')
        user.iss = claims.get('iss', '')
        user.oidc = claims.get('oidc', '')
        user.eppn = claims.get('eppn', '')
        user.eptid = claims.get('eptid', '')
        user.acr = claims.get('acr', '')
        user.affiliation = claims.get('affiliation', '')
        user.name = claims.get('name', '')
        user.show_uuid = False
        user.save()

        ldap_attributes = get_ldap_attributes(user)

        if ldap_attributes:
            check_ismemberof(ldap_attributes)
            update_membership_ismemberof(user, ldap_attributes)
            check_ldapother_attributes(ldap_attributes)
            update_ldapother_ismemberof(user, ldap_attributes)

        # generate welcome message
        subject = 'Welcome'
        body = 'Hello ' + str(user.name) + ', welcome to the Notary Service!'
        reference_url = 'https://ns-dev-1.cyberimpact.us'
        is_active = True
        ns_message = {
            "ns-message": {'subject': subject, 'body': body, 'reference_url': reference_url, 'is_active': is_active}}
        # print('topic: ' + str(user.uuid) + ', message: ' + str(ns_message))
        send_ns_message(str(user.uuid), ns_message)

        # set roles
        self.set_user_roles(user)
        user.roles.add(int(getattr(Role, 'NO_ROLE')))
        user.is_norole = True
        user.save()
        self.update_affiliation(user)

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.given_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.family_name = claims.get('family_name', '')
        user.idp = claims.get('idp', '')
        user.idp_name = claims.get('idp_name', '')
        user.sub = claims.get('sub', '')
        user.aud = claims.get('aud', '')
        user.cert_subject_dn = claims.get('cert_subject_dn', '')
        user.iss = claims.get('iss', '')
        user.oidc = claims.get('oidc', '')
        user.eppn = claims.get('eppn', '')
        user.eptid = claims.get('eptid', '')
        user.acr = claims.get('acr', '')
        user.affiliation = claims.get('affiliation', '')
        user.name = claims.get('name', '')
        user.save()

        ldap_attributes = get_ldap_attributes(user)

        if ldap_attributes:
            check_ismemberof(ldap_attributes)
            update_membership_ismemberof(user, ldap_attributes)
            check_ldapother_attributes(ldap_attributes)
            update_ldapother_ismemberof(user, ldap_attributes)

        # set roles
        self.set_user_roles(user)
        user.save()

        return user

    def update_affiliation(self, user):
        if not Affiliation.objects.filter(idp=user.idp).exists():
            Affiliation.objects.create(
                display_name=user.idp_name,
                idp_name=user.idp_name,
                idp=user.idp,
            )
