import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


def user_nstemplates_directory_path(instance, filename):
    # file will be uploaded to MEDIA_ROOT/user_<id>/<filename>
    return 'nstemplates/user_{0}/{1}'.format(instance.created_by.id, filename)


class NSTemplate(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    graphml_definition = models.FileField(upload_to=user_nstemplates_directory_path)
    description = models.TextField()
    is_valid = models.BooleanField(default=False)
    created_by = models.ForeignKey(User, related_name='nstemplate_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='nstemplate_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Template Description'

    def __str__(self):
        return self.name


class Dataset(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    dataset_identifier_as_url = models.URLField()
    dataset_identifier_as_doi_or_meta = models.URLField()
    safe_identifier_as_scid = models.CharField(max_length=255)
    description = models.TextField()
    is_valid = models.BooleanField(default=False)
    templates = models.ManyToManyField(NSTemplate, through="MembershipNSTemplate")
    created_by = models.ForeignKey(User, related_name='dataset_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='dataset_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Dataset Description'

    def __str__(self):
        return self.name


class MembershipNSTemplate(models.Model):
    template = models.ForeignKey(NSTemplate, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'NS Template'
