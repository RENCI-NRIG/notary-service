from django.contrib import admin
from .models import Project, MembershipComanage, ComanageGroup, MembershipWorkflow, WorkflowNeo4j


class ListProjects(admin.ModelAdmin):
    list_display = [
        'name',
        'uuid',
        'created_date',
        'modified_date',
    ]


admin.site.register(Project, ListProjects)


class ListCOmanageGroups(admin.ModelAdmin):
    project = Project.name
    comanage_group = ComanageGroup.cn
    list_display = [
        'project',
        'comanage_group'
    ]


admin.site.register(MembershipComanage, ListCOmanageGroups)


class ListWorkflows(admin.ModelAdmin):
    project = Project.name
    workflow = WorkflowNeo4j.name
    list_display = [
        'project',
        'workflow'
    ]


admin.site.register(MembershipWorkflow, ListWorkflows)
