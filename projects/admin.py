from django.contrib import admin

from .models import Project, ComanagePIAdmin, ComanageStaff, \
    MembershipComanagePIAdmin, MembershipComanageStaff, \
    WorkflowNeo4j, MembershipWorkflow


class ListProjects(admin.ModelAdmin):
    list_display = [
        'name',
        'uuid',
        'created_date',
        'modified_date',
    ]


admin.site.register(Project, ListProjects)


class ListComanagePIAdmin(admin.ModelAdmin):
    project = Project.name
    comanage_group = ComanagePIAdmin.cn
    list_display = [
        'project',
        'comanage_group',
    ]


admin.site.register(MembershipComanagePIAdmin, ListComanagePIAdmin)


class ListCOmanageMembers(admin.ModelAdmin):
    project = Project.name
    comanage_group = ComanageStaff.cn
    list_display = [
        'project',
        'comanage_group',
    ]


admin.site.register(MembershipComanageStaff, ListCOmanageMembers)


class ListWorkflows(admin.ModelAdmin):
    project = Project.name
    workflow = WorkflowNeo4j.name
    list_display = [
        'project',
        'workflow',
    ]


admin.site.register(MembershipWorkflow, ListWorkflows)
