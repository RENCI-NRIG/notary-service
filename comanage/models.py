# from django.contrib.auth.models import AbstractUser
from django.db import models

from users.models import NotaryServiceUser


class IsMemberOf(models.Model):
    attribute = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    members = models.ManyToManyField(NotaryServiceUser, through="MembershipIsMemberOf")

    def __str__(self):
        return self.value


class MembershipIsMemberOf(models.Model):
    user = models.ForeignKey(NotaryServiceUser, on_delete=models.CASCADE)
    ismemberof = models.ForeignKey(IsMemberOf, on_delete=models.CASCADE)


class LdapOther(models.Model):
    attribute = models.CharField(max_length=200)
    value = models.CharField(max_length=200)
    members = models.ManyToManyField(NotaryServiceUser, through="MembershipLdapOther")

    def __str__(self):
        return self.value


class MembershipLdapOther(models.Model):
    user = models.ForeignKey(NotaryServiceUser, on_delete=models.CASCADE)
    ldapother = models.ForeignKey(LdapOther, on_delete=models.CASCADE)
