import uuid
from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model
User = get_user_model()


class NSTemplate(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    graphml_definition = models.FilePathField()
    description = models.TextField()
    created_by = models.ForeignKey(User, related_name='nstemplate_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='nstemplate_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Template Description'

    def publish(self):
        self.modified_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    dataset_identifier = models.URLField(primary_key=False, editable=False)
    safe_identifier = models.CharField(max_length=255)
    description = models.TextField()
    templates = models.ManyToManyField(NSTemplate, through="MembershipNSTemplate")
    created_by = models.ForeignKey(User, related_name='dataset_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='dataset_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Dataset Description'

    def publish(self):
        self.modified_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name


class MembershipNSTemplate(models.Model):
    template = models.ForeignKey(NSTemplate, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'NS Template'
