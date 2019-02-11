from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import TemplateForm
from .models import NSTemplate
from ns_workflow import Neo4jWorkflow, WorkflowError
import os


def datasets(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_detail(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_new(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_edit(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def dataset_delete(request):
    context = {"datasets_page": "active"}
    return render(request, 'datasets.html', context)


def template_validate(graphml_file, template_uuid):
    bolt_url = os.getenv('NEO4J_BOLT_URL')
    neo_user = os.getenv('NEO4J_USER')
    neo_pass = os.getenv('NEO4J_PASS')
    import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
    import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')
    graphmlFile = open('./media/' + graphml_file, "r")
    graphml = graphmlFile.read()
    graphmlFile.close()
    workflow = Neo4jWorkflow(url=bolt_url,
                             user=neo_user,
                             pswd=neo_pass,
                             importDir=import_dir,
                             importHostDir=import_host_dir
                             )
    gid = workflow.import_workflow(graphml=graphml, graphId=template_uuid)
    print(gid)
    try:
        workflow.validate_workflow(graphId=gid)
    except WorkflowError as template_error:
        workflow.delete_workflow(graphId=gid)
        print(template_error)
        return False, template_error
    workflow.delete_workflow(graphId=gid)
    return True, None


def templates(request):
    context = {"templates_page": "active"}
    if request.user.is_authenticated:
        return template_list(request)
    else:
        return render(request, 'templates.html', context)


def template_list(request):
    templates = NSTemplate.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return render(request, 'templates.html', {'templates_page': 'active', 'templates': templates})


def template_detail(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    f = open(template.graphml_definition.path)
    template_file = f.read()
    f.close()
    if request.method == "POST":
        template.is_valid, template_error = template_validate(template.graphml_definition.name, str(template.uuid))
        template.save()
    else:
        template_error = None
    return render(request, 'template_detail.html', {
        'templates_page': 'active',
        'template': template,
        'template_file': template_file,
        'template_error': template_error,
    })


def template_new(request):
    if request.method == "POST":
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.created_by = request.user
            template.modified_by = request.user
            template.modified_date = timezone.now()
            template.save()
            return redirect('template_detail', uuid=template.uuid)
    else:
        form = TemplateForm()
    return render(request, 'template_edit.html', {'templates_page': 'active', 'form': form})


def template_edit(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    if request.method == "POST":
        form = TemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            template = form.save(commit=False)
            template.modified_by = request.user
            template.modified_date = timezone.now()
            template.is_valid = False
            template.save()
            return redirect('template_detail', uuid=template.uuid)
    else:
        form = TemplateForm(instance=template)
    return render(request, 'template_edit.html', {'templates_page': 'active', 'form': form})


def template_delete(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    if request.method == "POST":
        template.graphml_definition.delete()
        template.delete()
        return template_list(request)
    return render(request, 'template_delete.html', {
        'templates_page': 'active',
        'template': template,
    })
