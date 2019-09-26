from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from projects.models import MembershipProjectWorkflow, ComanagePersonnel, ProjectWorkflowUserCompletionByRole
from projects.workflows import take_user_through_workflow, \
    workflow_save_safe_token_and_complete, workflow_update_node_property, \
    workflow_make_conditional_selection_and_disable_branches
from workflows import workflow_neo4j as wf
from .context_processors import export_neo4j_vars
from .models import WorkflowNeo4j
from users.models import Role


def workflows(request):
    neo4j_vars = export_neo4j_vars(request)
    if request.user.is_authenticated:
        wf_objs = workflow_list(request)
        return render(request, 'workflows.html',
                      {'projects_page': 'active', 'workflows': wf_objs, 'neo4j_vars': neo4j_vars})
    return render(request, 'workflows.html', {"projects_page": "active", "neo4j_vars": neo4j_vars})


def workflow_list(request):
    try:
        person = ComanagePersonnel.objects.get(
            uid=request.user.sub,
        )
    except ComanagePersonnel.DoesNotExist:
        person = None

    if request.user.is_nsadmin:
        wf_objs = WorkflowNeo4j.objects.filter(created_date__lte=timezone.now()).order_by('name')
    elif request.user.is_ig:
        wf_objs = WorkflowNeo4j.objects.filter(
            uuid__in=ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid').filter(
                person=request.user,
                role=Role.objects.get(id=request.user.role)
            )
        ).order_by('name')
    elif request.user.is_dp:
        wf_objs = WorkflowNeo4j.objects.filter(
            uuid__in=ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid').filter(
                person=request.user,
                role=Role.objects.get(id=request.user.role)
            )
        ).order_by('name')
    elif request.user.is_inp:
        wf_objs = WorkflowNeo4j.objects.filter(
            uuid__in=ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid').filter(
                person=request.user,
                role=Role.objects.get(id=request.user.role)
            )
        ).order_by('name')
    elif request.user.is_piadmin:
        wf_objs = []
    elif request.user.is_pi:
        wf_objs = WorkflowNeo4j.objects.filter(
            uuid__in=ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid').filter(
                person=request.user,
                role=Role.objects.get(id=request.user.role)
            )
        ).order_by('name')
    elif request.user.is_nsstaff:
        wf_objs = WorkflowNeo4j.objects.filter(
            uuid__in=ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid').filter(
                person=request.user,
                role=Role.objects.get(id=request.user.role)
            )
        ).order_by('name')
    else:
        print('---- shouldn\'t get here ----')
        wf_objs = WorkflowNeo4j.objects.filter(created_date__lte=timezone.now()).order_by('name')

    return wf_objs


def workflow_detail(request, uuid):
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    workflow_graph = wf.get_neo4j_workflow_by_uuid(str(uuid))
    return render(request, 'workflow_detail.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'workflow_graph': workflow_graph,
    })


def workflow_delete(request, uuid):
    workflow = get_object_or_404(WorkflowNeo4j, uuid=uuid)
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    workflow_graph = wf.get_neo4j_workflow_by_uuid(str(uuid))
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
    })


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
    return render(request, 'workflow_reset.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'workflow_graph': workflow_graph,
    })


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
    workflow_graph = wf.get_neo4j_workflow_by_uuid_and_role(
        workflow_uuid=str(uuid),
        role_id=request.user.role,
        user_dn=request.user.cert_subject_dn
    )
    return render(request, 'workflow_access.html', {
        'projects_page': 'active',
        'workflow': workflow,
        'project': project,
        'assertions': assertions,
        'workflow_graph': workflow_graph
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
