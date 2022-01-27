import unicodedata
from typing import Optional

from mozilla_django_oidc.auth import OIDCAuthenticationBackend

from comanage import api
from comanage.comanage_api import add_co_person_roles, verify_ns_person_roles, add_co_affiliation, verify_ns_affiliation
from nsmessages.nsmessages import send_welcome_message


def generate_username(email):
    return unicodedata.normalize('NFKC', email)[:150]


class MyOIDCAB(OIDCAuthenticationBackend):

    def create_user(self, claims):
        user = super(MyOIDCAB, self).create_user(claims)
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.co_oidc_sub = claims.get('sub', '')
        user.eppn = claims.get('eppn', '')
        user.name = claims.get('name', '')
        user.cert_subject_dn = claims.get('cert_subject_dn', '')
        user.display_name = '{0} ({1})'.format(claims.get('name', ''), claims.get('email', ''))
        user.save()
        co_person_id = self.get_user_co_person_id(
            given_name=user.first_name, family_name=user.last_name, mail=user.email)
        if co_person_id:
            user.co_person_id = co_person_id
            user.is_active = True
            user.save()
            add_co_person_roles(co_person={'Id': user.co_person_id})
            add_co_affiliation(co_person={'Id': user.co_person_id})
            verify_ns_person_roles(ns_person=user)
            verify_ns_affiliation(ns_person=user)
        else:
            user.co_person_id = None
            user.is_active = True
        user.save()
        send_welcome_message(user=user)

        return user

    def update_user(self, user, claims):
        user.first_name = claims.get('given_name', '')
        user.last_name = claims.get('family_name', '')
        user.co_oidc_sub = claims.get('sub', '')
        user.eppn = claims.get('eppn', '')
        user.name = claims.get('name', '')
        user.cert_subject_dn = claims.get('cert_subject_dn', '')
        if not user.display_name:
            user.display_name = '{0} ({1})'.format(claims.get('name', ''), claims.get('email', ''))
        user.save()
        if not user.co_person_id:
            co_person_id = self.get_user_co_person_id(
                given_name=user.first_name, family_name=user.last_name, mail=user.email)
            if co_person_id:
                user.co_person_id = co_person_id
                user.is_active = True
                user.save()
                add_co_person_roles(co_person={'Id': user.co_person_id})
                add_co_affiliation(co_person={'Id': user.co_person_id})
                verify_ns_person_roles(ns_person=user)
                verify_ns_affiliation(ns_person=user)
            else:
                user.co_person_id = None
                user.is_active = True
            user.save()

        return user

    def get_user_co_person_id(self, given_name: str = None, family_name: str = None, mail: str = None) -> Optional[int]:
        try:
            if mail:
                co_person = api.copeople_match(mail=mail).get('CoPeople', [])
            else:
                co_person = api.copeople_match(given=given_name, family=family_name).get('CoPeople', [])
            if co_person:
                return int(co_person[0].get('Id'))
            else:
                return None
        except Exception as e:
            print(e)
            return None

    def set_user_roles(self, user):
        pass

    def update_affiliation(self, user):
        pass
