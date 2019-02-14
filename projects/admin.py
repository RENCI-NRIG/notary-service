from django.contrib import admin

from .models import Project, ComanageAdmin, ComanageMemberActive, \
    MembershipComanageAdmin, MembershipComanageMemberActive, \
    WorkflowNeo4j, MembershipWorkflow


class ListProjects(admin.ModelAdmin):
    list_display = [
        'name',
        'uuid',
        'created_date',
        'modified_date',
    ]


admin.site.register(Project, ListProjects)


class ListCOmanageAdmin(admin.ModelAdmin):
    project = Project.name
    comanage_group = ComanageAdmin.cn
    list_display = [
        'project',
        'comanage_group',
    ]


admin.site.register(MembershipComanageAdmin, ListCOmanageAdmin)


class ListCOmanageMembers(admin.ModelAdmin):
    project = Project.name
    comanage_group = ComanageMemberActive.cn
    list_display = [
        'project',
        'comanage_group',
    ]


admin.site.register(MembershipComanageMemberActive, ListCOmanageMembers)


class ListWorkflows(admin.ModelAdmin):
    project = Project.name
    workflow = WorkflowNeo4j.name
    list_display = [
        'project',
        'workflow',
    ]


admin.site.register(MembershipWorkflow, ListWorkflows)
