import json
import os

from django import template
from ns_workflow import Neo4jWorkflow

from projects.models import ProjectWorkflowUserCompletionByRole
from users.models import Role
from workflows.models import WorkflowNeo4j

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')
register = template.Library()


@register.filter
def workflow_status_is_completed(request, workflow_uuid):
    """
    :param request:
    :param workflow_uuid:
    :return:
    """
    if not ProjectWorkflowUserCompletionByRole.objects.filter(
            person=request.user.id,
            workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
    ).exists():
        return 'Unknown'
    if not ProjectWorkflowUserCompletionByRole.objects.filter(
            person=request.user.id,
            workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
            role=request.user.role,
    ).exists():
        return 'Role N/A'
    else:
        if ProjectWorkflowUserCompletionByRole.objects.get(
                person=request.user.id,
                workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
                role=request.user.role,
        ).is_complete:
            return 'True'
    return 'False'


@register.filter
def workflow_rolenames(workflow_uuid):
    """
    :param workflow_uuid:
    :return:
    """
    wf_obj = WorkflowNeo4j.objects.get(uuid=workflow_uuid)
    role_list = ''
    for role in wf_obj.roles.filter(workflowneo4j=wf_obj):
        role_list += role.get_id_display() + ', '
    return role_list.rstrip(', ')


@register.filter
def workflow_role_included(role_id, workflow_uuid):
    """
    :param role_id:
    :param workflow_uuid:
    :return:
    """
    role = str(Role.objects.get(id=role_id))
    return role in workflow_rolenames(workflow_uuid)


@register.filter
def workflow_is_complete(request, workflow_uuid):
    """
    :param request:
    :param workflow_uuid:
    :return:
    """
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    is_complete = n.is_workflow_complete(
        principalId=str(request.user.uuid),
        role=request.user.role,
        graphId=str(workflow_uuid),
    )
    return is_complete


@register.filter
def workflow_json_safe_parameters(safe_parameters):
    return json.loads(safe_parameters)


@register.filter
def workflow_safe_parameters_key_value(kv_pair):
    key = ''
    value = ''
    for k, v in kv_pair.items():
        key = k
        value = v
    return {'key': key, 'value': value}
