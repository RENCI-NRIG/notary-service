import uuid

from django.contrib.auth import get_user_model
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone

from datasets.models import Dataset, NSTemplate
from infrastructure.models import Infrastructure
from workflows.models import WorkflowNeo4j

User = get_user_model()


# Create your models here.
class ComanageStaff(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'COmanage Staff'

    def __str__(self):
        return self.cn[7:]


class ComanagePIAdmin(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'COmanage PI Admin'

    def __str__(self):
        return self.cn[7:]


class ComanagePersonnel(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    eppn = models.CharField(max_length=255)
    employee_number = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'COmanage Person'

    def __str__(self):
        return self.cn


class Project(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    description = models.TextField()
    is_valid = models.BooleanField(default=False)
    affiliation = ArrayField(models.CharField(max_length=255))
    idp = ArrayField(models.CharField(max_length=255))
    infrastructure = models.ManyToManyField(Infrastructure, through="MembershipInfrastructure")
    comanage_pi_admins = models.ManyToManyField(ComanagePIAdmin, through="MembershipComanagePIAdmin")
    comanage_staff = models.ManyToManyField(ComanageStaff, through="MembershipComanageStaff")
    comanage_personnel = models.ManyToManyField(ComanagePersonnel, through="MembershipComanagePersonnel")
    datasets = models.ManyToManyField(Dataset, through="MembershipDatasets")
    workflows = models.ManyToManyField(WorkflowNeo4j, through="MembershipWorkflow")
    created_by = models.ForeignKey(User, related_name='project_created_by', on_delete=models.CASCADE)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='project_modified_by', on_delete=models.CASCADE)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Project'

    def __str__(self):
        return self.name


class MembershipDatasets(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership Dataset'


class MembershipComanageStaff(models.Model):
    comanage_group = models.ForeignKey(ComanageStaff, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage Active Member'


class MembershipComanagePIAdmin(models.Model):
    comanage_group = models.ForeignKey(ComanagePIAdmin, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage Admin'


class MembershipWorkflow(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    template = models.ForeignKey(NSTemplate, on_delete=models.CASCADE)
    workflow = models.ForeignKey(WorkflowNeo4j, on_delete=models.CASCADE)
    is_generated = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Membership Workflow'


class MembershipComanagePersonnel(models.Model):
    person = models.ForeignKey(ComanagePersonnel, on_delete=models.CASCADE)
    comanage_pi_admins = models.ForeignKey(ComanagePIAdmin, on_delete=models.CASCADE, null=True)
    comanage_staff = models.ForeignKey(ComanageStaff, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage Person'


class MembershipInfrastructure(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership Infrastructure'
