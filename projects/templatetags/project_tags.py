from django import template

from workflows.models import WorkflowNeo4j

register = template.Library()


@register.filter
def workflow_rolenames(workflow_uuid):
    wf_obj = WorkflowNeo4j.objects.get(uuid=workflow_uuid)
    role_list = ''
    for role in wf_obj.roles.filter(workflowneo4j=wf_obj):
        role_list += role.get_id_display() + ', '
    return role_list.rstrip(', ')
