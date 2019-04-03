import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class Infrastructure(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    description = models.TextField()
    affiliation = models.CharField(max_length=255)
    is_valid = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='infrastructure_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='infrastructure_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'Infrastructure'

    def __str__(self):
        return self.name
