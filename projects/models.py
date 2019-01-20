import uuid
from django.db import models
from django.utils import timezone


# Create your models here.
class ComanageGroup(models.Model):
    dn = models.CharField(max_length=255)
    cn = models.CharField(max_length=255)
    active = models.BooleanField(default=False)

    def __unicode__(self):
        return self.cn[7:]

    def __str__(self):
        return self.cn[7:]


class WorkflowNeo4j(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    description = models.TextField()

    def __unicode__(self):
        return self.name

    def __str__(self):
        return self.name


class Project(models.Model):
    name = models.CharField(max_length=255)
    uuid = models.UUIDField(primary_key=False, default=uuid.uuid4, editable=False)
    description = models.TextField()
    comanage_groups = models.ManyToManyField(ComanageGroup, through="MembershipComanage")
    workflows = models.ManyToManyField(WorkflowNeo4j, through="MembershipWorkflow")
    created_date = models.DateTimeField(default=timezone.now)
    modified_date = models.DateTimeField(blank=True, null=True)

    class Meta:
        verbose_name = 'NS Project Description'

    def publish(self):
        self.modified_date = timezone.now()
        self.save()

    def __str__(self):
        return self.name


class MembershipComanage(models.Model):
    comanage_group = models.ForeignKey(ComanageGroup, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'NS Project Membership'


class MembershipWorkflow(models.Model):
    workflow = models.ForeignKey(WorkflowNeo4j, on_delete=models.CASCADE)
    project = models.ForeignKey(Project, on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'NS Project Workflow'
