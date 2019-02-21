import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from datasets.models import NSTemplate, Dataset

User = get_user_model()


class WorkflowNeo4j(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    description = models.TextField()
    dataset = models.ForeignKey(Dataset, related_name='workflow_dataset', on_delete=models.CASCADE)
    template = models.ForeignKey(NSTemplate, related_name='workflow_template', on_delete=models.CASCADE)
    created_by = models.ForeignKey(User, related_name='workflow_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='workflow_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)
    loaded_in_neo4j = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Neo4j Workflow'

    def publish(self):
        self.modified_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name
