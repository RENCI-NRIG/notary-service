import json
import os

from django import template
from django.http import QueryDict
from ns_workflow import Neo4jWorkflow

from projects.models import ProjectWorkflowUserCompletionByRole, MembershipComanagePersonnel, Project
from projects.workflows import get_next_set_by_role, get_converted_user_roles_per_project_as_id
from users.models import WorkflowRole, Affiliation
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
def project_affiliations(request, project_uuid):
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    affiliations = ns_project.affiliation.all()

    return affiliations


@register.filter
def project_ig_assignment_by_affiliation(request, project_uuid):
    """
    return uuid of IG assigned to project
    :param request:
    :param project_uuid:
    :return:
    """
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    ns_affiliations = ns_project.affiliation.all().values_list('name', flat=True)
    ns_ig_affiliations = ns_project.project_igs.all().values_list('affiliation__name', flat=True)
    ig = {
        'is_affiliated': False,
        'is_assigned': False,
        'assigned_to': None
    }
    if request.user.affiliation.name in ns_affiliations:
        ig['is_affiliated'] = True
    else:
        ig['is_affiliated'] = False

    if ig['is_affiliated']:
        if request.user.affiliation.name in ns_ig_affiliations:
            ig['is_assigned'] = True
    else:
        ig['is_assigned'] = False

    if ig['is_assigned']:
        ig['assigned_to'] = ns_project.project_igs.filter(
            affiliation__name=request.user.affiliation.name
        ).first()
    else:
        ig['assigned_to'] = None

    return ig


@register.filter
def workflow_status_is_completed(request, workflow_uuid):
    """
    :param request:
    :param workflow_uuid:
    :return:
    """
    # print('### workflow_status_is_completed ###')
    ns_wf = WorkflowNeo4j.objects.filter(uuid=workflow_uuid).first()
    # print(ns_wf)
    # ns_project = WorkflowNeo4j.objects.filter(project__workflows__in=[ns_wf.id]).values('project').first()
    ns_project = Project.objects.filter(workflows__uuid__in=[ns_wf.uuid]).first()
    # print(ns_project)
    if ns_project:
        project_uuid = ns_project.uuid
        user_roles = get_converted_user_roles_per_project_as_id(project=ns_project, user=request.user)
    else:
        project_uuid = ''
        user_roles = []

    if not ProjectWorkflowUserCompletionByRole.objects.filter(
            person=request.user.id,
            workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
    ).exists():
        return 'Unknown'
    if not ProjectWorkflowUserCompletionByRole.objects.filter(
            person=request.user.id,
            workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
            role__in=user_roles,
    ).exists():
        return 'Role N/A'
    else:
        for role in user_roles:
            next_set = get_next_set_by_role(user_obj=request.user, workflow=str(workflow_uuid), role=role)
            if len(next_set) != 0:
                continue
                # return 'False'
            else:
                return str(workflow_is_complete(request=request, workflow_uuid=str(workflow_uuid), project_uuid=project_uuid))
        return 'False'


@register.filter()
def workflow_waiting_on_others(request, workflow_uuid):
    next_set = get_next_set_by_role(user_obj=request.user, workflow=str(workflow_uuid))
    if len(next_set) == 0:
        return 'True'
    else:
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
    role = str(WorkflowRole.objects.get(id=role_id))
    return role in workflow_rolenames(workflow_uuid)


@register.filter
def workflow_is_complete(request, project_uuid, workflow_uuid):
    """
    :param request:
    :param workflow_uuid:
    :return:
    """
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    user_roles = get_converted_user_roles_per_project_as_id(project=ns_project, user=request.user)
    n = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importHostDir=import_host_dir,
        importDir=import_dir,
    )
    is_complete = False
    for role in user_roles:
        is_complete = n.is_workflow_complete(
            principalId=str(request.user.uuid),
            role=role,
            graphId=str(workflow_uuid),
        )
        if not is_complete:
            is_complete = False
            break

    return is_complete


@register.filter
def dataset_all_workflows_complete(request, project_uuid, dataset_uuid):
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    user_roles = get_converted_user_roles_per_project_as_id(project=ns_project, user=request.user)
    wf_uuid_list = ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid', flat=True).filter(
        project__uuid=project_uuid,
        dataset__uuid=dataset_uuid,
        role__in=user_roles
    )
    if len(wf_uuid_list) == 0:
        return False
    for wf_uuid in wf_uuid_list:
        if not workflow_is_complete(request=request, project_uuid=project_uuid, workflow_uuid=wf_uuid):
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
    :return: key, value as JSON
    """
    key = ''
    value = ''
    for k, v in kv_pair.items():
        key = k
        value = v
    return {'key': key, 'value': value}


@register.filter
def dataset_workflows_completed_button_status(request, dataset_obj):
    """
    Check for dataset access by validating all workflows related
    to the user / role / dataset / project are completed
    :param request:
    :param dataset_obj:
    :return:
    """
    # project_uuid passed in GET request (data_access.html)
    project_uuid = request.GET.get('project_uuid', '-1')
    if project_uuid == '-1':
        # project_uuid is part of the URI (project_details.html)
        project_uuid = str(request.build_absolute_uri()).rpartition('/')[-1]

    ns_project = Project.objects.filter(uuid=project_uuid).first()
    user_roles = get_converted_user_roles_per_project_as_id(project=ns_project, user=request.user)

    workflow_list = ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid', flat=True).filter(
        person=request.user,
        role__in=user_roles,
        project=Project.objects.get(uuid=project_uuid),
        dataset=dataset_obj
    )
    if len(workflow_list) == 0:
        return False
    for workflow_uuid in workflow_list:
        status = workflow_status_is_completed(request, str(workflow_uuid))
        if status != 'True':
            return False
    return True
