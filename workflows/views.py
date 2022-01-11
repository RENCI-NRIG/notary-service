from itertools import chain

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from datasets.models import Dataset
from projects.models import MembershipProjectWorkflow
from projects.models import Project
from projects.workflows import take_user_through_workflow, \
    workflow_save_safe_token_and_complete, workflow_update_node_property, \
    workflow_make_conditional_selection_and_disable_branches
from workflows import workflow_neo4j as wf
from .context_processors import export_neo4j_vars
from .models import WorkflowNeo4j


@login_required()
def workflows(request):
    neo4j_vars = export_neo4j_vars(request)
    if request.user.is_authenticated:
        wf_objs = workflow_list(request)
        return render(request, 'workflows.html',
                      {'projects_page': 'active', 'workflows': wf_objs, 'neo4j_vars': neo4j_vars})
    return render(request, 'workflows.html', {"projects_page": "active", "neo4j_vars": neo4j_vars})


def workflow_list(request):
    wf_objs = []

    if request.user.is_nsadmin():
        wf_objs = WorkflowNeo4j.objects.filter(created_date__lte=timezone.now()).order_by('name')
    elif request.user.is_dp():
        wf_objs = WorkflowNeo4j.objects.filter(created_date__lte=timezone.now()).order_by('name')
    elif request.user.is_inp():
        wf_objs = []
    elif request.user.is_pi():
        wf_objs = []
    elif request.user.is_ig():
        wf_objs = []

    return wf_objs


@login_required()
def workflow_detail(request, uuid):
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    ns_project = Project.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).project_id
    ).first()
    ns_dataset = Dataset.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).dataset_id
    ).first()
    workflow_graph = wf.get_neo4j_workflow_by_uuid(str(uuid))
    ns_piadmins = ns_project.comanage_pi_admins.all()
    ns_pis = ns_project.comanage_pi_members.all()
    ns_staff = ns_project.comanage_staff.all()
    ns_igs = ns_project.project_igs.all()
    ns_inp = ns_project.infrastructure.owner
    ns_dso = ns_dataset.owner
    members_set = list(chain(ns_piadmins, ns_pis, ns_staff, ns_igs))
    members_set.append(ns_inp)
    members_set.append(ns_dso)
    project_pis = list(chain(ns_piadmins, ns_pis))
    return render(request, 'workflow_detail.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'workflow_graph': workflow_graph,
        'members_set': members_set,
        'project_pis': project_pis
    })


@login_required()
def workflow_delete(request, uuid):
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    ns_project = Project.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).project_id
    ).first()
    workflow_graph = wf.get_neo4j_workflow_by_uuid(str(uuid))
    ns_piadmins = ns_project.comanage_pi_admins.all()
    ns_pis = ns_project.comanage_pi_members.all()
    project_pis = list(chain(ns_piadmins, ns_pis))
    if request.method == "POST":
        if request.POST.get("workflow_delete"):
            delete_neo4j_workflow(
                workflow_uuid=str(uuid)
            )
            workflow.delete()
        return redirect('project_detail', uuid=project.project.uuid)
    return render(request, 'workflow_delete.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'workflow_graph': workflow_graph,
        'project_pis': project_pis
    })


@login_required()
def workflow_reset(request, uuid):
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    workflow_graph = wf.get_neo4j_workflow_by_uuid(str(uuid))
    if request.method == "POST":
        if request.POST.get("workflow_reset"):
            graphml_file = workflow.template.graphml_definition.name
            workflow_uuid = str(uuid)
            delete_neo4j_workflow(
                workflow_uuid
            )
            is_reset = create_neo4j_workflow(
                graphml_file,
                workflow_uuid
            )
            if is_reset:
                return redirect('workflow_detail', uuid=workflow.uuid)
        return redirect('project_detail', uuid=project.project.uuid)
    ns_project = Project.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).project_id
    ).first()
    ns_piadmins = ns_project.comanage_pi_admins.all()
    ns_pis = ns_project.comanage_pi_members.all()
    project_pis = list(chain(ns_piadmins, ns_pis))
    return render(request, 'workflow_reset.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'workflow_graph': workflow_graph,
        'project_pis': project_pis
    })


@login_required()
def workflow_access(request, uuid):
    """
    template objects for workflow_access.html
    :param request:
    :param uuid:
    :return:
    """
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    if request.method == "POST":
        for key, value in request.POST.items():
            if 'cond_singleselection_' in key:
                workflow_make_conditional_selection_and_disable_branches(
                    graph_id=str(uuid),
                    node_id=key.split('cond_singleselection_', 1)[1],
                    cond_value=str(value)
                )
                workflow_save_safe_token_and_complete(
                    graph_id=str(uuid),
                    node_id=key.split('cond_singleselection_', 1)[1],
                    user_dn=request.user.cert_subject_dn
                )
            elif 'assert_singleselection_' in key:
                workflow_update_node_property(
                    graph_id=str(uuid),
                    node_id=key.split('assert_singleselection_', 1)[1],
                    prop_name='ParameterValue',
                    prop_value=str(value)
                )
                workflow_save_safe_token_and_complete(
                    graph_id=str(uuid),
                    node_id=key.split('assert_singleselection_', 1)[1],
                    user_dn=request.user.cert_subject_dn
                )
            elif 'assert_string_' in key:
                if str(value).rstrip('\r\n') != '':
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('assert_string_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value=str(value).rstrip('\r\n')
                    )
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('assert_string_', 1)[1],
                        user_dn=request.user.cert_subject_dn
                    )
            elif 'assert_stringlist_' in key:
                if str(value).rstrip('\r\n') != '':
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('assert_stringlist_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value=str(value).rstrip('\r\n').split('\r\n')
                    )
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('assert_stringlist_', 1)[1],
                        user_dn=request.user.cert_subject_dn
                    )
            elif 'assert_ipv4list_' in key:
                if str(value).rstrip('\r\n') != '':
                    # TODO: FQDN or IP validation on value
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('assert_ipv4list_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value=str(value).rstrip('\r\n').split('\r\n')
                    )
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('assert_ipv4list_', 1)[1],
                        user_dn=request.user.cert_subject_dn
                    )
            elif 'assert_multiselection_' in key:
                value_list = ''
                for item in request.POST.getlist(key):
                    value_list += str(item) + ', '
                if str(value).rstrip('\r\n') != '':
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('assert_multiselection_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value=value_list.rstrip(', ')
                    )
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('assert_multiselection_', 1)[1],
                        user_dn=request.user.cert_subject_dn
                    )
            elif 'checkbox_' in key:
                if value == 'on':
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('checkbox_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value='True'
                    )
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('checkbox_', 1)[1],
                        user_dn=request.user.cert_subject_dn
                    )
                else:
                    workflow_update_node_property(
                        graph_id=str(uuid),
                        node_id=key.split('checkbox_', 1)[1],
                        prop_name='ParameterValue',
                        prop_value='False'
                    )
        workflow.modified_date = timezone.now()
        workflow.save()
    project = MembershipProjectWorkflow.objects.get(
        workflow__uuid=workflow.uuid
    )
    assertions = take_user_through_workflow(
        user_obj=request.user,
        workflow=str(workflow.uuid)
    )
    # print(assertions)
    # workflow_graph = wf.get_neo4j_workflow_by_uuid_and_role(
    #     workflow_uuid=str(uuid),
    #     role_id=request.user.role,
    #     user_dn=request.user.cert_subject_dn
    # )
    workflow_graph = wf.get_neo4j_workflow_by_uuid(
        workflow_uuid=str(uuid)
    )
    ns_project = Project.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).project_id
    ).first()
    ns_dataset = Dataset.objects.filter(
        id=MembershipProjectWorkflow.objects.get(workflow_id=workflow.id).dataset_id
    ).first()
    ns_piadmins = ns_project.comanage_pi_admins.all()
    ns_pis = ns_project.comanage_pi_members.all()
    ns_staff = ns_project.comanage_staff.all()
    ns_igs = ns_project.project_igs.all()
    ns_inp = ns_project.infrastructure.owner
    ns_dso = ns_dataset.owner
    members_set = list(chain(ns_piadmins, ns_pis, ns_staff, ns_igs))
    members_set.append(ns_inp)
    members_set.append(ns_dso)
    return render(request, 'workflow_access.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'assertions': assertions,
        'workflow_graph': workflow_graph,
        'members_set': members_set
    })


def create_neo4j_workflow(graphml_file, workflow_uuid):
    """
    create neo4j workflow
    :param graphml_file:
    :param workflow_uuid:
    :return:
    """
    wf_created = wf.create_workflow_from_template(
        graphml_file=graphml_file,
        workflow_uuid=workflow_uuid,
    )
    return wf_created


def delete_neo4j_workflow(workflow_uuid):
    """
    delete neo4j workflow
    :param workflow_uuid:
    :return:
    """
    wf.delete_workflow_by_uuid(workflow_uuid)
