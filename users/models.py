import os
import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from core.mixins import AuditModelMixin
from core.models import BaseModel


ns_roles = [
    os.getenv('ROLE_IMPACT_USER'),
    os.getenv('ROLE_DP'),
    os.getenv('ROLE_INP'),
    os.getenv('ROLE_PI'),
    os.getenv('ROLE_IG'),
    os.getenv('ROLE_NSADMIN'),
    os.getenv('ROLE_ENROLLMENT_APPROVAL')
]


class Affiliation(BaseModel,
                  AuditModelMixin):
    name = models.CharField(max_length=255, blank=False)
    uuid = models.UUIDField(primary_key=False, null=True, blank=True)
    co_affiliation_id = models.IntegerField()
    co_person_id = models.IntegerField()


class ComanageCou(BaseModel,
                  AuditModelMixin):
    name = models.CharField(max_length=255, blank=False)
    description = models.CharField(max_length=255, default='', blank=True)
    co_cou_id = models.IntegerField()
    co_cou_parent_id = models.IntegerField(default=None, null=True, blank=True)


class Role(BaseModel,
           AuditModelMixin):
    co_role_id = models.IntegerField()
    co_person_id = models.IntegerField()
    co_cou = models.ForeignKey(
        'ComanageCou',
        on_delete=models.CASCADE,
    )


class CilogonCertificate(BaseModel, AuditModelMixin):
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    pubkey = models.TextField(null=True, blank=True)
    privkey = models.TextField(null=True, blank=True)
    csr = models.TextField(null=True, blank=True)
    p12 = models.BinaryField(null=True, blank=True)
    expires = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.pubkey


class NotaryServiceUser(BaseModel,
                        AuditModelMixin,
                        AbstractUser):
    first_name = models.CharField(
        max_length=64,
        default='',
        blank=True
    )
    last_name = models.CharField(
        max_length=64,
        default='',
        blank=True
    )
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    co_person_id = models.IntegerField(default=None, null=True, blank=True)
    co_oidc_sub = models.CharField(max_length=255, null=True, blank=True)
    cert_subject_dn = models.CharField(max_length=255, null=True, blank=True)
    cilogon_cert = models.ForeignKey('CilogonCertificate', on_delete=models.DO_NOTHING, null=True, blank=True)
    name = models.CharField(max_length=255)
    display_name = models.CharField(max_length=255)
    eppn = models.CharField(max_length=255)
    affiliation = models.ForeignKey(
        'Affiliation',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True
    )
    roles = models.ManyToManyField(Role)

    def is_impact_user(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_IMPACT_USER')).exists()

    def is_dp(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_DP')).exists()

    def is_inp(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_INP')).exists()

    def is_pi(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_PI')).exists()

    def is_ig(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_IG')).exists()

    def is_nsadmin(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_NSADMIN')).exists()

    def is_enrollment_approval(self) -> bool:
        return self.roles.filter(co_cou__name=os.getenv('ROLE_ENROLLMENT_APPROVAL')).exists()

    def __str__(self):
        return self.display_name


class WorkflowRole(models.Model):
    """
    The Role entries are managed by the system
    """
    NSADMIN = 1  # CO:COU:NOTARY_SERVICE-NSADMIN:admins
    STAFF = 2  # CO:COU:PROJECT_NAME-STAFF:members:active
    DP = 3  # CO:COU:PROJECT_NAME-DP:members:active
    INP = 4  # CO:COU:PROJECT_NAME-INP:members:active
    IG = 5  # CO:COU:PROJECT_NAME-IG:members:active
    PI_ADMIN = 6  # CO:COU:PROJECT_NAME-PI:admins
    PI_MEMBER = 7  # CO:COU:PROJECT_NAME-PI:members:active
    NO_ROLE = 8  # No role found in COmanage
    ROLE_CHOICES = (
        (NSADMIN, 'Administrator'),
        (STAFF, 'Project Member'),
        (DP, 'Data Provider'),
        (INP, 'Infrastructure Provider'),
        (IG, 'Institutional Governance'),
        (PI_ADMIN, 'Project PI Admin'),
        (PI_MEMBER, 'Project PI'),
        (NO_ROLE, 'No Role'),
    )

    id = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, primary_key=True)

    def __str__(self):
        return self.get_id_display()


# class Affiliation(models.Model):
#     """
#     Affiliation of the user based on Identity Provider or Admin manual entry
#     """
#     uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
#     display_name = models.CharField(max_length=255)
#     idp = models.CharField(max_length=255)
#     idp_name = models.CharField(max_length=255)
#
#     def __str__(self):
#         return self.display_name
#
#     def __len__(self):
#         return len(self.display_name)
#
#
# class CILogonCertificate(models.Model):
#     use_my_key = models.BooleanField(default=False)
#     public_key_path = models.FilePathField(null=True, blank=True, default=None)
#     private_key_path = models.FilePathField(null=True, blank=True, default=None)
#     pkcs12_file_path = models.FilePathField(null=True, blank=True, default=None)
#     authorization_response = models.CharField(max_length=1024)
#
#
# class NotaryServiceUser(AbstractUser):
#     """
#     Extends AbstractUser
#     - username
#     - first_name
#     - last_name
#     - email
#     - is_staff
#     - is_active
#     """
#     uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
#     display_name = models.CharField(max_length=255, blank=True, null=True)
#     co_person_id = models.IntegerField(primary_key=False, blank=False, null=False)
#     given_name = models.CharField(max_length=255)
#     family_name = models.CharField(max_length=255)
#     idp = models.CharField(max_length=255)
#     idp_name = models.CharField(max_length=255)
#     sub = models.CharField(max_length=255)
#     aud = models.CharField(max_length=255)
#     cert_subject_dn = models.CharField(max_length=255)
#     iss = models.CharField(max_length=255)
#     oidc = models.CharField(max_length=255)
#     eppn = models.CharField(max_length=255)
#     eptid = models.CharField(max_length=255)
#     acr = models.CharField(max_length=255)
#     affiliation = models.CharField(max_length=255)
#     ns_affiliation = models.CharField(max_length=255)
#     name = models.CharField(max_length=255)
#     show_uuid = models.BooleanField(default=False)
#     roles = models.ManyToManyField(Role)
#     role = models.PositiveSmallIntegerField(default=Role.NO_ROLE)
#     is_nsadmin = models.BooleanField(default=False)
#     is_nsstaff = models.BooleanField(default=False)
#     is_pi = models.BooleanField(default=False)
#     is_piadmin = models.BooleanField(default=False)
#     is_dp = models.BooleanField(default=False)
#     is_inp = models.BooleanField(default=False)
#     is_ig = models.BooleanField(default=False)
#     is_norole = models.BooleanField(default=False)
#     cilogon_certificate_date = models.DateTimeField(null=True, blank=True, default=None)
#     cilogon_auth_code = models.CharField(max_length=1024)
#     cilogon_auth_state = models.CharField(max_length=255)
#
#     def __str__(self):
#         return self.email
