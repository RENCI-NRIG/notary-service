import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Role(models.Model):
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


class NotaryServiceUser(AbstractUser):
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    given_name = models.CharField(max_length=255)
    family_name = models.CharField(max_length=255)
    idp = models.CharField(max_length=255)
    idp_name = models.CharField(max_length=255)
    sub = models.CharField(max_length=255)
    aud = models.CharField(max_length=255)
    cert_subject_dn = models.CharField(max_length=255)
    iss = models.CharField(max_length=255)
    oidc = models.CharField(max_length=255)
    eppn = models.CharField(max_length=255)
    eptid = models.CharField(max_length=255)
    acr = models.CharField(max_length=255)
    affiliation = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    show_uuid = models.BooleanField(default=False)
    roles = models.ManyToManyField(Role)
    role = models.PositiveSmallIntegerField(default=Role.NO_ROLE)
    is_nsadmin = models.BooleanField(default=False)
    is_nsstaff = models.BooleanField(default=False)
    is_pi = models.BooleanField(default=False)
    is_piadmin = models.BooleanField(default=False)
    is_dp = models.BooleanField(default=False)
    is_inp = models.BooleanField(default=False)
    is_ig = models.BooleanField(default=False)
    is_norole = models.BooleanField(default=False)

    def __str__(self):
        return self.email


class Affiliation(models.Model):
    """
    Affiliation of the user based on Identity Provider or Admin manual entry
    """
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    display_name = models.CharField(max_length=255)
    idp = models.CharField(max_length=255)
    idp_name = models.CharField(max_length=255)

    def __str__(self):
        return self.display_name
