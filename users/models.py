import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class NotaryServiceUser(AbstractUser):
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    given_name = models.CharField(max_length=200)
    family_name = models.CharField(max_length=200)
    idp = models.CharField(max_length=200)
    idp_name = models.CharField(max_length=200)
    sub = models.CharField(max_length=200)
    aud = models.CharField(max_length=200)
    cert_subject_dn = models.CharField(max_length=200)
    iss = models.CharField(max_length=200)
    oidc = models.CharField(max_length=200)
    eppn = models.CharField(max_length=200)
    eptid = models.CharField(max_length=200)
    acr = models.CharField(max_length=200)
    affiliation = models.CharField(max_length=200)
    name = models.CharField(max_length=200)
    show_uuid = models.BooleanField(default=False)

    def __str__(self):
        return self.email
