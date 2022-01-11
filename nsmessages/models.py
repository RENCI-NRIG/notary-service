import uuid

from django.db import models

from core.mixins import AuditModelMixin
from core.models import BaseModel
from users.models import NotaryServiceUser


class NsMessages(BaseModel, AuditModelMixin):
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    subject = models.CharField(max_length=255, blank=False)
    body = models.TextField(blank=True, null=True)
    users_to = models.ManyToManyField(NotaryServiceUser, related_name='nsmessages_to')
    users_from = models.ManyToManyField(NotaryServiceUser, related_name='nsmessages_from')
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return self.subject
