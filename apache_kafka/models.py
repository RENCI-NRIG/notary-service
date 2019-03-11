import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from users.models import NotaryServiceUser

User = get_user_model()


class Message(models.Model):
    subject = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    body = models.TextField()
    reference_url = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    created_by = models.CharField(max_length=255, default='System Account')
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.CharField(max_length=255, default='System Account')
    modified_date = models.DateTimeField(blank=True, null=True)
    kafka_topic = models.CharField(max_length=255, blank=True, null=True)
    kafka_partition = models.IntegerField(blank=True, null=True)
    kafka_offset = models.IntegerField(blank=True, null=True)
    kafka_key = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        verbose_name = 'NS Message'

    def publish(self):
        self.modified_date = timezone.now()
        self.save()

    def __str__(self):
        return self.subject
