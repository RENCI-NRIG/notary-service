import unicodedata

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from .ldapsearch import get_ldap_attributes
from .models import IsMemberOf, MembershipIsMemberOf, LdapOther, MembershipLdapOther


def generate_username(email):
    return unicodedata.normalize('NFKC', email)[:150]


def check_ismemberof(attributelist):
    print('### CHECKING ISMEMBEROF')
    if attributelist['isMemberOf']:
        for attribute in attributelist['isMemberOf']:
            if not IsMemberOf.objects.filter(value=attribute).exists():
                IsMemberOf.objects.create(attribute='isMemberOf', value=attribute)


def update_membership_ismemberof(user, attributelist):
    print('### UPDATE ISMEMBEROF')
    for attribute in attributelist['isMemberOf']:
        attr_id = IsMemberOf.objects.get(attribute='isMemberOf', value=attribute).pk
        if not MembershipIsMemberOf.objects.filter(user=user.id, ismemberof=attr_id).exists():
            MembershipIsMemberOf.objects.create(user=user, ismemberof=IsMemberOf.objects.get(id=attr_id))


def check_ldapother_attributes(attributelist):
    print('### CHECKING LDAPOTHER')
    # print(attributelist['eduPersonAffiliation'])
    if attributelist['eduPersonAffiliation']:
        for attribute in attributelist['eduPersonAffiliation']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='eduPersonAffiliation', value=attribute)
    # print(attributelist['eduPersonPrincipalName'])
    if attributelist['eduPersonPrincipalName']:
        for attribute in attributelist['eduPersonPrincipalName']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='eduPersonPrincipalName', value=attribute)
    # print(attributelist['objectClass'])
    if attributelist['objectClass']:
        for attribute in attributelist['objectClass']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='objectClass', value=attribute)
    # print(attributelist['uid'])
    if attributelist['uid']:
        for attribute in attributelist['uid']:
            if not LdapOther.objects.filter(value=attribute).exists():
                LdapOther.objects.create(attribute='uid', value=attribute)


def update_ldapother_ismemberof(user, attributelist):
    print('### UPDATE LDAPOTHER')
    for attribute in attributelist['eduPersonAffiliation']:
        attr_id = LdapOther.objects.get(attribute='eduPersonAffiliation', value=attribute).pk
        if not MembershipLdapOther.objects.filter(user=user.id, ldapother=attr_id).exists():
            MembershipLdapOther.objects.create(user=user, ldapother=LdapOther.objects.get(id=attr_id))
    for attribute in attributelist['eduPersonPrincipalName']:
        attr_id = LdapOther.objects.get(attribute='eduPersonPrincipalName', value=attribute).pk
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
    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)

        print('### CREATE USER')
        print(claims)

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

        ldap_attributes = get_ldap_attributes(claims.get('email', ''))

        if ldap_attributes:
            check_ismemberof(ldap_attributes)
            update_membership_ismemberof(user, ldap_attributes)
            check_ldapother_attributes(ldap_attributes)
            update_ldapother_ismemberof(user, ldap_attributes)

        return user

    def update_user(self, user, claims):

        print('### UPDATE USER')
        print(claims)

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

        ldap_attributes = get_ldap_attributes(claims.get('email', ''))

        if ldap_attributes:
            check_ismemberof(ldap_attributes)
            update_membership_ismemberof(user, ldap_attributes)
            check_ldapother_attributes(ldap_attributes)
            update_ldapother_ismemberof(user, ldap_attributes)

        return user
