from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from projects.models import MembershipProjectWorkflow
from projects.workflows import take_user_through_workflow, \
    workflow_save_safe_token_and_complete, workflow_update_node_property
from workflows import workflow_neo4j as wf
from .context_processors import export_neo4j_vars
from .models import WorkflowNeo4j


def workflows(request):
    neo4j_vars = export_neo4j_vars(request)
    if request.user.is_authenticated:
        wf_objs = workflow_list(request)
        return render(request, 'workflows.html',
                      {'projects_page': 'active', 'workflows': wf_objs, 'neo4j_vars': neo4j_vars})
    return render(request, 'workflows.html', {"projects_page": "active", "neo4j_vars": neo4j_vars})


def workflow_list(request):
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
            if 'single_select_' in key:
                workflow_update_node_property(
                    graph_id=str(uuid),
                    node_id=key.split('single_select_', 1)[1],
                    prop_name='ParameterValue',
                    prop_value=str(value)
                )
                workflow_save_safe_token_and_complete(
                    graph_id=str(uuid),
                    node_id=key.split('single_select_', 1)[1],
                )
            elif 'checkbox_' in key:
                if value == 'on':
                    workflow_save_safe_token_and_complete(
                        graph_id=str(uuid),
                        node_id=key.split('checkbox_', 1)[1],
                    )
    project = MembershipProjectWorkflow.objects.get(workflow__uuid=workflow.uuid)
    assertions = take_user_through_workflow(user=request.user, workflow=str(workflow.uuid))
    workflow_graph = wf.get_neo4j_workflow_by_uuid_and_role(str(uuid), request.user.role, request.user.uuid)
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
