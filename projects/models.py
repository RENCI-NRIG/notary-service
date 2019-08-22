import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

from datasets.models import Dataset, NSTemplate
from infrastructure.models import Infrastructure
from users.models import Affiliation, NotaryServiceUser, Role
from workflows.models import WorkflowNeo4j

User = get_user_model()


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


class ComanagePIMember(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    active = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'COmanage PI Member'

    def __str__(self):
        return self.cn[7:]


class ComanagePersonnel(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    eppn = models.CharField(max_length=255)
    employee_number = models.CharField(max_length=255)
    email = models.CharField(max_length=255)
    active = models.BooleanField(default=False)
    uid = models.CharField(max_length=255)

    class Meta:
        verbose_name = 'COmanage Person'

    def __str__(self):
        return self.cn


class Project(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    comanage_name = models.CharField(max_length=255)
    description = models.TextField()
    is_valid = models.BooleanField(default=False)
    affiliations = models.ManyToManyField(Affiliation, through="MembershipAffiliations")
    infrastructure = models.ManyToManyField(Infrastructure, through="MembershipInfrastructure")
    comanage_pi_admins = models.ManyToManyField(ComanagePIAdmin, through="MembershipComanagePIAdmin")
    comanage_pi_members = models.ManyToManyField(ComanagePIMember, through="MembershipComanagePIMember")
    comanage_staff = models.ManyToManyField(ComanageStaff, through="MembershipComanageStaff")
    comanage_personnel = models.ManyToManyField(ComanagePersonnel, through="MembershipComanagePersonnel")
    datasets = models.ManyToManyField(Dataset, through="MembershipDatasets")
    workflows = models.ManyToManyField(WorkflowNeo4j, through="MembershipProjectWorkflow")
    created_by = models.ForeignKey(User, related_name='project_created_by', on_delete=models.CASCADE, null=True,
                                   blank=True)
    created_date = models.DateTimeField(default=timezone.now)
    modified_by = models.ForeignKey(User, related_name='project_modified_by', on_delete=models.CASCADE, null=True,
                                    blank=True)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Project'

    def __str__(self):
        return self.name


class MembershipAffiliations(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership Affiliation'


class MembershipDatasets(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership Dataset'


class MembershipComanageStaff(models.Model):
    comanage_group = models.ForeignKey(ComanageStaff, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage Staff'


class MembershipComanagePIAdmin(models.Model):
    comanage_group = models.ForeignKey(ComanagePIAdmin, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage PI Admin'


class MembershipComanagePIMember(models.Model):
    comanage_group = models.ForeignKey(ComanagePIMember, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage PI Member'


class MembershipProjectWorkflow(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    affiliation = models.ForeignKey(Affiliation, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    template = models.ForeignKey(NSTemplate, on_delete=models.CASCADE)
    workflow = models.ForeignKey(WorkflowNeo4j, on_delete=models.CASCADE)
    is_generated = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Membership Project Workflow'


class MembershipInfrastructure(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    infrastructure = models.ForeignKey(Infrastructure, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership Infrastructure'


class MembershipComanagePersonnel(models.Model):
    person = models.ForeignKey(ComanagePersonnel, on_delete=models.CASCADE)
    comanage_pi_admins = models.ForeignKey(ComanagePIAdmin, on_delete=models.CASCADE, null=True)
    comanage_pi_members = models.ForeignKey(ComanagePIMember, on_delete=models.CASCADE, null=True)
    comanage_staff = models.ForeignKey(ComanageStaff, on_delete=models.CASCADE, null=True)
    infrastructure_inp = models.ForeignKey(MembershipInfrastructure, on_delete=models.CASCADE, null=True)
    affiliation_ig = models.ForeignKey(Affiliation, on_delete=models.CASCADE, null=True)
    dataset_dso = models.ForeignKey(MembershipDatasets, on_delete=models.CASCADE, null=True)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Membership COmanage Personnel'


class ProjectWorkflowUserCompletionByRole(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    dataset = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    workflow = models.ForeignKey(WorkflowNeo4j, on_delete=models.CASCADE)
    person = models.ForeignKey(NotaryServiceUser, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    is_complete = models.BooleanField(default=False)

    class Meta:
        verbose_name = 'Project Workflow User Completion by Role'
