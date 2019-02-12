from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import TemplateForm, DatasetForm
from .models import NSTemplate, Dataset, MembershipNSTemplate
from ns_workflow import Neo4jWorkflow, WorkflowError
import os


def datasets(request):
    context = {"datasets_page": "active"}
    if request.user.is_authenticated:
        return dataset_list(request)
    else:
        return render(request, 'datasets.html', context)


def dataset_list(request):
    ds_objs = Dataset.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return render(request, 'datasets.html', {'datasets_page': 'active', 'datasets': ds_objs})


def dataset_validate(tp_list):
    for name, is_valid, uuid, file in tp_list:
        if not is_valid:
            return False, 'Template ' + str(uuid) + ' is not validated'
    return True, None


def dataset_detail(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    tp_list = list(MembershipNSTemplate.objects.values_list(
        'template__name',
        'template__is_valid',
        'template__uuid',
        'template__graphml_definition',
    ).filter(
        dataset=dataset,
    ))
    if request.method == "POST":
        dataset.is_valid, dataset_error = dataset_validate(tp_list)
        dataset.save()
    else:
        dataset_error = None
    return render(request, 'dataset_detail.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'dataset_error': dataset_error,
        'templates': tp_list,
    })


def dataset_new(request):
    if request.method == "POST":
        form = DatasetForm(request.POST)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.created_by = request.user
            dataset.modified_by = request.user
            dataset.modified_date = timezone.now()
            dataset.save()
            for template_pk in form.data.getlist('templates'):
                if not MembershipNSTemplate.objects.filter(
                        dataset=dataset.id,
                        template=template_pk
                ).exists():
                    MembershipNSTemplate.objects.create(
                        dataset=dataset,
                        template=NSTemplate.objects.get(id=template_pk)
                    )
            return redirect('dataset_detail', uuid=dataset.uuid)
    else:
        form = DatasetForm()
    return render(request, 'dataset_edit.html', {'datasets_page': 'active', 'form': form})


def dataset_edit(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    if request.method == "POST":
        form = DatasetForm(request.POST, instance=dataset)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.created_by = request.user
            dataset.modified_by = request.user
            dataset.modified_date = timezone.now()
            dataset.is_valid = False
            dataset.save()
            membership = MembershipNSTemplate.objects.filter(dataset=dataset.id)
            for member in membership:
                if str(member.template.id) not in form.data.getlist('templates'):
                    MembershipNSTemplate.objects.filter(
                        dataset=dataset.id,
                        template=member.template.id
                    ).delete()
            for template_pk in form.data.getlist('templates'):
                if not MembershipNSTemplate.objects.filter(
                        dataset=dataset.id,
                        template=template_pk
                ).exists():
                    MembershipNSTemplate.objects.create(
                        dataset=dataset,
                        template=NSTemplate.objects.get(id=template_pk)
                    )
            return redirect('dataset_detail', uuid=dataset.uuid)
    else:
        form = DatasetForm(instance=dataset)
    return render(request, 'dataset_edit.html', {'datasets_page': 'active', 'form': form})


def dataset_delete(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    tp_list = list(MembershipNSTemplate.objects.values_list(
        'template__name',
        'template__is_valid',
        'template__uuid',
        'template__graphml_definition',
    ).filter(
        dataset=dataset,
    ))
    used_by = dataset_in_use(uuid)
    if request.method == "POST":
        dataset.delete()
        return dataset_list(request)
    return render(request, 'dataset_delete.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'used_by': used_by,
        'templates': tp_list,
    })


def dataset_in_use(template_uuid):
    proj_list = MembershipNSTemplate.objects.values_list(
        'dataset__uuid',
    ).filter(
        template__uuid=template_uuid,
    )
    proj_objs = Dataset.objects.filter(uuid__in=proj_list)
    return proj_objs


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
    tp_objs = NSTemplate.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return render(request, 'templates.html', {'templates_page': 'active', 'templates': tp_objs})


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
            update_dataset_status_by_template(template.uuid)
            return redirect('template_detail', uuid=template.uuid)
    else:
        form = TemplateForm(instance=template)
    return render(request, 'template_edit.html', {'templates_page': 'active', 'form': form})


def template_delete(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    used_by = template_in_use(uuid)
    if request.method == "POST":
        template.graphml_definition.delete()
        template.delete()
        return template_list(request)
    return render(request, 'template_delete.html', {
        'templates_page': 'active',
        'template': template,
        'used_by': used_by
    })


def update_dataset_status_by_template(uuid):
    ds_list = MembershipNSTemplate.objects.values(
        'dataset__uuid'
    ).filter(template__uuid=uuid)
    for ds_uuid in ds_list:
        ds = Dataset.objects.get(uuid=ds_uuid['dataset__uuid'])
        ds.is_valid = False
        ds.save()


def template_in_use(template_uuid):
    ds_list = MembershipNSTemplate.objects.values_list(
        'dataset__uuid',
    ).filter(
        template__uuid=template_uuid,
    )
    ds_objs = Dataset.objects.filter(uuid__in=ds_list)
    return ds_objs
