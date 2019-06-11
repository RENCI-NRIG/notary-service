from django.shortcuts import render, get_object_or_404, redirect, render_to_response
from django.utils import timezone
from .context_processors import export_neo4j_vars
from .models import WorkflowNeo4j
from projects.models import MembershipProjectWorkflow
from workflows import workflow_neo4j as wf
from json import dumps



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


def create_neo4j_workflow(graphml_file, workflow_uuid):
    wf_created = wf.create_workflow_from_template(
        graphml_file=graphml_file,
        workflow_uuid=workflow_uuid,
    )
    return wf_created


def delete_neo4j_workflow(workflow_uuid):
    wf.delete_workflow_by_uuid(workflow_uuid)
