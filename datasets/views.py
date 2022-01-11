import os

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from itertools import chain

from datasets.models import Dataset
from ns_workflow import Neo4jWorkflow, WorkflowError
from projects.models import Project, MembershipDatasets, ProjectWorkflowUserCompletionByRole, \
    MembershipProjectWorkflow
from projects.workflows import get_next_set_by_role, workflow_report_from_neo4j
from safe.post_assertions import get_id_from_pub, post_raw_idset, post_common_completion_receipt, \
    post_user_completion_receipt, post_link_receipt_for_dataset
from workflows.models import WorkflowNeo4j
from workflows.workflow_neo4j import create_workflow_from_template, delete_workflow_by_uuid, \
    get_neo4j_workflow_by_uuid
from .forms import TemplateForm, DatasetForm
from .jwt import encode_ns_jwt, decode_ns_jwt
from .models import NSTemplate, MembershipNSTemplate
from projects.workflows import get_converted_user_roles_per_project_as_id

bolt_url = os.getenv('NEO4J_BOLT_URL')
neo_user = os.getenv('NEO4J_USER')
neo_pass = os.getenv('NEO4J_PASS')
import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')


# *** DATASETS ***
@login_required()
def datasets(request):
    my_datasets = Dataset.objects.filter(
        created_by__in=[request.user]
    ).order_by('name').distinct()
    other_datasets = Dataset.objects.all().difference(my_datasets).order_by('name')

    return render(request, 'datasets.html', {
        'datasets_page': 'active', 'my_datasets': my_datasets, 'other_datasets': other_datasets
    })


def dataset_validate(dataset_obj, show_uuid):
    tpl_objs = NSTemplate.objects.filter(
        uuid__in=Dataset.objects.values_list(
            'templates__uuid',
            flat=True
        ).filter(
            uuid=dataset_obj.uuid
        )
    )
    if len(tpl_objs) != 2:
        return False, 'Dataset must contain exactly two templates (research_approval and infrastructure_approval)'
    type_list = []
    for type in tpl_objs.values_list('type', flat=True):
        type_list.append(type)
    if 'research_approval' not in type_list:
        return False, 'Dataset must contain a template of type "research_approval"'
    if 'infrastructure_approval' not in type_list:
        return False, 'Dataset must contain a template of type "infrastructure_approval"'
    for template in tpl_objs:
        if not template.is_valid:
            if show_uuid:
                return False, 'Template ' + str(template.uuid) + ' is not validated'
            else:
                return False, 'Template (' + str(template.description)[:34] + '..) is not validated'
    return True, None


@login_required()
def dataset_detail(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    tpl_list = MembershipNSTemplate.objects.values_list(
        'template__uuid',
    ).filter(
        dataset=dataset,
    )
    tpl_objs = NSTemplate.objects.filter(uuid__in=tpl_list).order_by('name')
    if request.method == "POST":
        dataset.is_valid, dataset_error = dataset_validate(dataset, False)
        dataset.save()
    else:
        dataset_error = None
    return render(request, 'dataset_detail.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'dataset_error': dataset_error,
        'templates': tpl_objs,
    })


def dataset_post_safe_receipts(principal, user, project, dataset, workflow1, workflow2):
    r1 = post_raw_idset(principal=principal)
    r2 = post_common_completion_receipt(principal=principal, project=project, workflow=workflow1)
    r3 = post_user_completion_receipt(principal=principal, user=user, project=project, workflow=workflow1)
    r4 = post_common_completion_receipt(principal=principal, project=project, workflow=workflow2)
    r5 = post_user_completion_receipt(principal=principal, user=user, project=project, workflow=workflow2)
    r6 = post_link_receipt_for_dataset(principal=principal, user=user, project=project, dataset=dataset,
                                       workflow=workflow1)
    r7 = post_link_receipt_for_dataset(principal=principal, user=user, project=project, dataset=dataset,
                                       workflow=workflow2)

    return [r1, r2, r3, r4, r5, r6, r7]


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


# def workflow_status_is_completed(request, workflow_uuid: str, project_uuid: str):
#     """
#     :param request:
#     :param workflow_uuid:
#     :return:
#     """
#     ns_project = Project.objects.filter(
#         uuid=project_uuid
#     ).first()
#     user_roles = get_converted_user_roles_per_project_as_id(project=ns_project, user=request.user)
#
#     for role in user_roles:
#         if not ProjectWorkflowUserCompletionByRole.objects.filter(
#                 person=request.user.id,
#                 workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
#         ).exists():
#             return 'Unknown'
#         if not ProjectWorkflowUserCompletionByRole.objects.filter(
#                 person=request.user.id,
#                 workflow=WorkflowNeo4j.objects.get(uuid=workflow_uuid),
#                 # role=request.user.role,
#         ).exists():
#             return 'Role N/A'
#         else:
#             next_set = get_next_set_by_role(user_obj=request.user, workflow=str(workflow_uuid), role=role)
#             if len(next_set) != 0:
#                 return 'False'
#
#     return str(workflow_is_complete(request=request, workflow_uuid=workflow_uuid))


def dataset_are_workflows_completed(request, dataset_obj):
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

    workflow_list = ProjectWorkflowUserCompletionByRole.objects.values_list('workflow__uuid', flat=True).filter(
        person=request.user,
        # role=request.user.role,
        project=Project.objects.get(uuid=project_uuid),
        dataset=dataset_obj
    )
    workflow_list = list(set(workflow_list))
    if len(workflow_list) == 0:
        return False
    for workflow_uuid in workflow_list:
        is_complete = workflow_is_complete(request, project_uuid, workflow_uuid)
        if not is_complete:
            return False

    return True


@login_required()
def dataset_access(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    dataset_error = None
    # ns_project = Project.objects.filter(uuid=request.GET.get('project_uuid')).first()
    ns_project = get_object_or_404(Project, uuid=request.GET.get('project_uuid'))
    project_uuid = str(ns_project.uuid)
    project_name = ns_project.name
    # project_uuid = request.GET.get('project_uuid', '-1')
    # project_name = Project.objects.get(uuid=project_uuid).name
    if dataset_are_workflows_completed(request, dataset):
        safe_principal = get_id_from_pub(os.getenv('SAFE_PRINCIPAL_PUBKEY', './safe/keys/ns.pub'))
        safe_user = request.user.cert_subject_dn
        # safe_project = project_uuid
        safe_project = str(ns_project.uuid)
        safe_dataset = dataset.safe_identifier_as_scid
        safe_workflow1, safe_workflow2 = Dataset.objects.values_list(
            'workflow_dataset__template__safe_identifier_as_scid',
            flat=True
        ).filter(
            uuid=dataset.uuid
        ).distinct()
        resp = dataset_post_safe_receipts(
            principal=safe_principal,
            user=safe_user,
            project=safe_project,
            dataset=safe_dataset,
            workflow1=safe_workflow1,
            workflow2=safe_workflow2
        )
        signed_jwt = encode_ns_jwt(
            project_uuid=project_uuid,
            dataset_scid=dataset.safe_identifier_as_scid,
            user=request.user
        )
        jwt_claims = decode_ns_jwt(signed_jwt)
    else:
        signed_jwt = ''
        jwt_claims = ''
    ns_piadmins = ns_project.comanage_pi_admins.all()
    ns_pis = ns_project.comanage_pi_members.all()
    ns_staff = ns_project.comanage_staff.all()
    ns_igs = ns_project.project_igs.all()
    ns_inp = ns_project.infrastructure.owner
    ns_dso = dataset.owner
    members_set = list(chain(ns_piadmins, ns_pis, ns_staff, ns_igs))
    members_set.append(ns_inp)
    members_set.append(ns_dso)
    return render(request, 'dataset_access.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'dataset_error': dataset_error,
        'project_uuid': project_uuid,
        'project_name': project_name,
        'project': ns_project,
        'signed_jwt': signed_jwt,
        'jwt_claims': jwt_claims,
        'members_set': members_set
    })


@login_required()
def dataset_report(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    dataset_error = None
    project_uuid = request.GET.get('project_uuid', '-1')
    project = Project.objects.get(uuid=project_uuid)
    workflow_uuid_list = WorkflowNeo4j.objects.values_list('uuid', flat=True).filter(
        uuid__in=MembershipProjectWorkflow.objects.values('workflow__uuid').filter(
            project=Project.objects.get(uuid=project_uuid),
            dataset=dataset
        )
    )
    workflow_reports = []
    for workflow_uuid in workflow_uuid_list:
        worflow_report = {}
        worflow_report['workflow'] = WorkflowNeo4j.objects.get(
            uuid=workflow_uuid
        )
        worflow_report['nodes'] = workflow_report_from_neo4j(workflow_uuid)
        workflow_reports.append(worflow_report)
    ns_piadmins = project.comanage_pi_admins.all()
    ns_pis = project.comanage_pi_members.all()
    ns_igs = project.project_igs.all()
    ns_dso = dataset.owner
    members_set = list(chain(ns_piadmins, ns_pis, ns_igs))
    members_set.append(ns_dso)

    return render(request, 'dataset_report.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'dataset_error': dataset_error,
        'project': project,
        'workflow_reports': workflow_reports,
        'user': request.user,
        'members_set': members_set
    })


def iframe_mock(request):
    return render(request, 'iframe_mock.html', {'home_page': 'active'})


@login_required()
def dataset_new(request):
    if request.method == "POST":
        form = DatasetForm(request.POST, request=request)
        if form.is_valid():
            dataset = form.save(commit=False)
            dataset.owner = request.user
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
        form = DatasetForm(request=request)
    return render(request, 'dataset_new.html', {'datasets_page': 'active', 'form': form})


@login_required()
def dataset_edit(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    if request.method == "POST":
        form = DatasetForm(request.POST, instance=dataset, request=request)
        if form.is_valid():
            dataset = form.save(commit=False)
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
            update_project_status_by_dataset(dataset.uuid)
            return redirect('dataset_detail', uuid=dataset.uuid)
    else:
        form = DatasetForm(instance=dataset, request=request)
    return render(request, 'dataset_edit.html', {'datasets_page': 'active', 'form': form, 'dataset': dataset})


@login_required()
def dataset_delete(request, uuid):
    dataset = get_object_or_404(Dataset, uuid=uuid)
    tpl_list = MembershipNSTemplate.objects.values_list(
        'template__uuid',
    ).filter(
        dataset=dataset,
    )
    tpl_objs = NSTemplate.objects.filter(uuid__in=tpl_list).order_by('name')
    used_by = dataset_in_use(uuid)
    if request.method == "POST":
        dataset.delete()
        return redirect('datasets')
    return render(request, 'dataset_delete.html', {
        'datasets_page': 'active',
        'dataset': dataset,
        'used_by': used_by,
        'templates': tpl_objs,
    })


def update_project_status_by_dataset(uuid):
    proj_list = MembershipDatasets.objects.values(
        'project__uuid'
    ).filter(dataset__uuid=uuid)
    for proj_uuid in proj_list:
        proj = Project.objects.get(uuid=proj_uuid['project__uuid'])
        proj.is_valid = False
        proj.save()


def dataset_in_use(ds_uuid):
    proj_list = MembershipDatasets.objects.values_list(
        'project__uuid',
    ).filter(
        dataset__uuid=ds_uuid,
    )
    proj_objs = Project.objects.filter(uuid__in=proj_list).order_by('name')
    return proj_objs


def template_validate(graphml_file, template_uuid):
    bolt_url = os.getenv('NEO4J_BOLT_URL')
    neo_user = os.getenv('NEO4J_USER')
    neo_pass = os.getenv('NEO4J_PASS')
    import_dir = os.getenv('NEO4J_IMPORTS_PATH_DOCKER')
    import_host_dir = os.getenv('NEO4J_IMPORTS_PATH_HOST')
    template_error = None
    is_valid = False
    try:
        delete_workflow_by_uuid(template_uuid)
    except WorkflowError as e:
        print(e)
        pass
    graphmlFile = open('./media/' + graphml_file, "r")
    graphml = graphmlFile.read()
    graphmlFile.close()
    workflow = Neo4jWorkflow(
        url=bolt_url,
        user=neo_user,
        pswd=neo_pass,
        importDir=import_dir,
        importHostDir=import_host_dir
    )
    gid = workflow.import_workflow(graphml=graphml, graphId=template_uuid)
    try:
        workflow.validate_workflow(graphId=gid)
    except WorkflowError as e:
        template_error = e
        is_valid = False
    workflow.delete_workflow(graphId=template_uuid)
    if template_error is None:
        create_workflow_from_template(graphml_file, template_uuid)
        is_valid = True
    return is_valid, template_error


# *** TEMPLATES ***
@login_required()
def templates(request):
    my_templates = NSTemplate.objects.filter(
        created_by__in=[request.user]
    ).order_by('name').distinct()
    other_templates = NSTemplate.objects.all().difference(my_templates).order_by('name')

    return render(request, 'templates.html', {
      'templates_page': 'active', 'my_templates': my_templates, 'other_templates': other_templates
    })


def template_list(request):
    tpl_objs = []
    if request.user.is_nsadmin():
        tpl_objs = NSTemplate.objects.filter(created_date__lte=timezone.now()).order_by('name')
    elif request.user.is_dp():
        tpl_objs = NSTemplate.objects.filter(
            owner=request.user
        ).order_by('name')
    elif request.user.is_inp():
        tpl_objs = []
    elif request.user.is_pi():
        tpl_objs = []
    elif request.user.is_ig():
        tpl_objs = []

    return render(request, 'templates.html', {'templates_page': 'active', 'templates': tpl_objs})


@login_required()
def template_detail(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    f = open(template.graphml_definition.path)
    template_file = f.read()
    f.close()
    template_error = None
    workflow_graph = get_neo4j_workflow_by_uuid(str(uuid))
    if request.method == "POST":
        if request.POST.get("validate-template"):
            template.is_valid, template_error = template_validate(template.graphml_definition.name, str(template.uuid))
            template.save()
            if template.is_valid:
                template.save()
                return redirect('template_detail', uuid=template.uuid)
    return render(request, 'template_detail.html', {
        'templates_page': 'active',
        'template': template,
        'template_file': template_file,
        'template_error': template_error,
        'workflow_graph': workflow_graph,
    })


@login_required()
def template_new(request):
    if request.method == "POST":
        form = TemplateForm(request.POST, request.FILES)
        if form.is_valid():
            template = form.save(commit=False)
            template.owner = request.user
            template.created_by = request.user
            template.modified_by = request.user
            template.modified_date = timezone.now()
            template.save()
            return redirect('template_detail', uuid=template.uuid)
    else:
        form = TemplateForm()
    return render(request, 'template_new.html', {'templates_page': 'active', 'form': form})


@login_required()
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
    return render(request, 'template_edit.html', {'templates_page': 'active', 'form': form, 'template': template})


@login_required()
def template_delete(request, uuid):
    template = get_object_or_404(NSTemplate, uuid=uuid)
    used_by = template_in_use(uuid)
    if request.method == "POST":
        delete_workflow_by_uuid(str(uuid))
        template.graphml_definition.delete()
        template.delete()
        return redirect('templates')
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
        update_project_status_by_dataset(ds.uuid)


def template_in_use(template_uuid):
    ds_list = MembershipNSTemplate.objects.values_list(
        'dataset__uuid',
    ).filter(
        template__uuid=template_uuid,
    )
    ds_objs = Dataset.objects.filter(uuid__in=ds_list).order_by('name')
    return ds_objs
