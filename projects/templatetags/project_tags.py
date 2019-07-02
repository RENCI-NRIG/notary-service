import json
import os

from django import template
from ns_workflow import Neo4jWorkflow

from projects.models import ProjectWorkflowUserCompletionByRole, MembershipComanagePersonnel, Project
from users.models import Role, Affiliation
from workflows.models import WorkflowNeo4j

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')
register = template.Library()


@register.filter
def project_ig_assignment(request, project_uuid):
    """
    return uuid of IG assigned to project
    :param request:
    :param project_uuid:
    :return:
    """
    if not MembershipComanagePersonnel.objects.filter(
            project=Project.objects.get(uuid=project_uuid),
            affiliation_ig=Affiliation.objects.get(uuid=request.user.ns_affiliation),
    ).exists():
        return 'False'
    else:
        return MembershipComanagePersonnel.objects.get(
            project=Project.objects.get(uuid=project_uuid),
            affiliation_ig=Affiliation.objects.get(uuid=request.user.ns_affiliation),
        ).person


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
        return str(workflow_is_complete(request=request, workflow_uuid=workflow_uuid))


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
def dataset_all_workflows_complete(request, project_uuid, dataset_uuid):
    wf_uuid_list = ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid', flat=True).filter(
        project__uuid=project_uuid,
        dataset__uuid=dataset_uuid,
        role=request.user.role
    )
    if len(wf_uuid_list) == 0:
        return False
    for wf_uuid in wf_uuid_list:
        if not workflow_is_complete(request=request, workflow_uuid=wf_uuid):
            return False
    return True


@register.filter
def workflow_json_safe_parameters(safe_parameters):
    """
    convert SAFE parameters from Neo4j property to JSON
    :param safe_parameters:
    :return:
    """
    return json.loads(safe_parameters)


@register.filter
def workflow_safe_parameters_key_value(kv_pair):
    """
    Return single key/value pair for parsing at the template level from kv_pair object
    :param kv_pair:
    :return:
    """
    key = ''
    value = ''
    for k, v in kv_pair.items():
        key = k
        value = v
    return {'key': key, 'value': value}
