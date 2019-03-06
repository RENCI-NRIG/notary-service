from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from datasets.models import Dataset, MembershipNSTemplate, NSTemplate
from workflows.models import WorkflowNeo4j
from users.models import NotaryServiceUser
from .forms import ProjectForm
from .models import Project, ComanageMemberActive, ComanageAdmin, MembershipComanageMemberActive, \
    MembershipComanageAdmin, MembershipComanagePersonnel, \
    MembershipDatasets, MembershipWorkflow
from .projects import update_comanage_group, personnel_by_comanage_group, update_comanage_personnel
from workflows import views as wf_views
from workflows.workflow_neo4j import delete_workflow_from_uuid



def projects(request):
    context = {"projects_page": "active"}
    if request.user.is_authenticated:
        return project_list(request)
    else:
        return render(request, 'projects.html', context)


def project_validate(ds_objs, show_uuid):
    for ds in ds_objs:
        if not ds.is_valid:
            if show_uuid:
                return False, 'Dataset ' + str(ds.uuid) + ' is not validated'
            else:
                return False, 'Dataset (' + str(ds.description)[:34] + '..) is not validated'
    return True, None


def project_detail(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    comanage_admins = ComanageAdmin.objects.filter(cn__contains=':admins', project=project).order_by('cn')
    comanage_groups = ComanageMemberActive.objects.filter(cn__contains=':active', project=project).order_by('cn')
    admin_group = list(MembershipComanagePersonnel.objects.values_list(
        'comanage_admins__cn',
        'person__cn',
        'person__employee_number',
        'person__eppn',
        'person__email',
    ).order_by(
        'comanage_admins__cn',
        'person__cn'
    ).filter(
        project=project,
        comanage_admins__in=comanage_admins
    ))
    member_group = list(MembershipComanagePersonnel.objects.values_list(
        'comanage_groups__cn',
        'person__cn',
        'person__employee_number',
        'person__eppn',
        'person__email'
    ).order_by(
        'comanage_groups__cn',
        'person__cn'
    ).filter(
        project=project,
        comanage_groups__in=comanage_groups
    ))
    ds_list = MembershipDatasets.objects.values_list('dataset__uuid').filter(project__uuid=uuid)
    ds_objs = Dataset.objects.filter(uuid__in=ds_list).order_by('name')
    project_error = None
    if request.method == "POST":
        if request.POST.get("validate"):
            project.is_valid, project_error = project_validate(ds_objs, request.user.show_uuid)
        elif request.POST.get("generate_workflow"):
            # delete workflows that are no longer part of the project
            wf_ds_list = MembershipWorkflow.objects.values_list('dataset__uuid').filter(project__uuid=uuid)
            wf_ds_objs = Dataset.objects.filter(uuid__in=wf_ds_list)
            for ds in wf_ds_objs:
                # check at dataset level
                if ds not in ds_objs:
                    rm_wf_list = MembershipWorkflow.objects.values_list('workflow__uuid').filter(
                        project=project, dataset=ds)
                    rm_wf_objs = WorkflowNeo4j.objects.filter(uuid__in=rm_wf_list)
                    for wf in rm_wf_objs:
                        delete_workflow_from_uuid(workflow_uuid=str(wf.uuid))
                        wf.delete()
                    MembershipWorkflow.objects.filter(project=project, dataset=ds).delete()
                else:
                    # check at template level
                    wf_tpl_list = MembershipWorkflow.objects.values_list('template__uuid').filter(project__uuid=uuid)
                    wf_tpl_objs = NSTemplate.objects.filter(uuid__in=wf_tpl_list)
                    for tpl in wf_tpl_objs:
                        if not MembershipNSTemplate.objects.filter(dataset=ds, template=tpl).exists():
                            rm_wf_list = MembershipWorkflow.objects.values_list('workflow__uuid').filter(
                                project=project, dataset=ds, template=tpl
                            )
                            rm_wf_objs = WorkflowNeo4j.objects.filter(uuid__in=rm_wf_list)
                            for wf in rm_wf_objs:
                                delete_workflow_from_uuid(workflow_uuid=str(wf.uuid))
                                wf.delete()
                                MembershipWorkflow.objects.filter(
                                    project=project, dataset=ds, template=tpl
                                ).delete()
            # create workflows as needed from updated project
            for ds in ds_objs:
                tpl_list = MembershipNSTemplate.objects.values_list('template__uuid').filter(dataset__uuid=ds.uuid)
                tpl_objs = NSTemplate.objects.filter(uuid__in=tpl_list).order_by('name')
                for tpl in tpl_objs:
                    if not MembershipWorkflow.objects.filter(
                            project=project, dataset=ds, template=tpl
                    ).exists():
                        create_new_workflow(
                            project_obj=project, dataset_obj=ds, template_obj=tpl, user_obj=request.user
                        )
        project.save()
    wf_list = MembershipWorkflow.objects.values_list('workflow__uuid').filter(project__uuid=project.uuid)
    wf_objs = WorkflowNeo4j.objects.filter(uuid__in=wf_list).order_by('name')
    return render(request, 'project_detail.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_admins': comanage_admins,
        'comanage_groups': comanage_groups,
        'admin_group': admin_group,
        'member_group': member_group,
        'datasets': ds_objs,
        'project_error': project_error,
        'workflows': wf_objs,
    })


def create_new_workflow(project_obj: Project,
                        dataset_obj: Dataset,
                        template_obj: NSTemplate,
                        user_obj: NotaryServiceUser):
    workflow = WorkflowNeo4j.objects.create(
        name='neo4j_',
        description=template_obj.description,
        dataset=dataset_obj,
        template=template_obj,
        created_by=user_obj,
        created_date=timezone.now(),
        modified_by=user_obj,
        modified_date=timezone.now(),
    )
    workflow.name = 'neo4j_' + str(workflow.uuid)
    workflow.save()
    wf_created = wf_views.create_neo4j_workflow(
        graphml_file=template_obj.graphml_definition.name,
        workflow_uuid=str(workflow.uuid)
    )
    if wf_created:
        workflow.loaded_in_neo4j = True
        workflow.save()
        MembershipWorkflow.objects.create(
            project=project_obj,
            dataset=dataset_obj,
            template=template_obj,
            workflow=workflow,
            is_generated=True,
        )


def project_list(request):
    projects = Project.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return render(request, 'projects.html', {'projects_page': 'active', 'projects': projects})


def project_new(request):
    update_comanage_group()
    update_comanage_personnel()
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.created_by = request.user
            project.modified_by = request.user
            project.modified_date = timezone.now()
            project.save()
            # admin groups
            for group_pk in form.data.getlist('comanage_admins'):
                if not MembershipComanageAdmin.objects.filter(project=project.id, comanage_group=group_pk).exists():
                    MembershipComanageAdmin.objects.create(
                        project=project,
                        comanage_group=ComanageAdmin.objects.get(id=group_pk)
                    )
                    personnel = personnel_by_comanage_group(ComanageAdmin.objects.get(id=group_pk).cn)
                    for person in personnel:
                        if not MembershipComanagePersonnel.objects.filter(
                                person=person,
                                project=project,
                                comanage_admins=ComanageAdmin.objects.get(id=group_pk)):
                            MembershipComanagePersonnel.objects.create(
                                person=person,
                                project=project,
                                comanage_admins=ComanageAdmin.objects.get(id=group_pk),
                                comanage_groups=None
                            )
            # membership groups
            for group_pk in form.data.getlist('comanage_groups'):
                if not MembershipComanageMemberActive.objects.filter(project=project.id,
                                                                     comanage_group=group_pk).exists():
                    MembershipComanageMemberActive.objects.create(
                        project=project,
                        comanage_group=ComanageMemberActive.objects.get(id=group_pk)
                    )
                    personnel = personnel_by_comanage_group(ComanageMemberActive.objects.get(id=group_pk).cn)
                    for person in personnel:
                        if not MembershipComanagePersonnel.objects.filter(
                                person=person,
                                project=project,
                                comanage_groups=ComanageMemberActive.objects.get(id=group_pk)):
                            MembershipComanagePersonnel.objects.create(
                                person=person,
                                project=project,
                                comanage_admins=None,
                                comanage_groups=ComanageMemberActive.objects.get(id=group_pk)
                            )
            # datasets
            for ds_pk in form.data.getlist('datasets'):
                if not MembershipDatasets.objects.filter(project=project.id, dataset=ds_pk).exists():
                    MembershipDatasets.objects.create(
                        project=project,
                        dataset=Dataset.objects.get(id=ds_pk)
                    )

            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectForm()
    return render(request, 'project_edit.html', {'projects_page': 'active', 'form': form})


def project_edit(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    update_comanage_group()
    if request.method == "POST":
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            project = form.save(commit=False)
            project.modified_by = request.user
            project.modified_date = timezone.now()
            project.save()

            # administrative groups
            current_groups = MembershipComanageAdmin.objects.filter(project=project.id)
            for group in current_groups:
                if str(group.comanage_group.id) not in form.data.getlist('comanage_admins'):
                    MembershipComanagePersonnel.objects.filter(project=project.id,
                                                               comanage_admins=group.comanage_group.id).delete()
                    group.delete()
            for group_pk in form.data.getlist('comanage_admins'):
                if not MembershipComanageAdmin.objects.filter(project=project.id, comanage_group=group_pk).exists():
                    MembershipComanageAdmin.objects.create(
                        project=project,
                        comanage_group=ComanageAdmin.objects.get(id=group_pk)
                    )
                    personnel = personnel_by_comanage_group(ComanageAdmin.objects.get(id=group_pk).cn)
                    for person in personnel:
                        if not MembershipComanagePersonnel.objects.filter(
                                person=person,
                                project=project,
                                comanage_admins=ComanageAdmin.objects.get(id=group_pk)):
                            MembershipComanagePersonnel.objects.create(
                                person=person,
                                project=project,
                                comanage_admins=ComanageAdmin.objects.get(id=group_pk),
                                comanage_groups=None
                            )
            # membership groups
            current_groups = MembershipComanageMemberActive.objects.filter(project=project.id)
            for group in current_groups:
                if str(group.comanage_group.id) not in form.data.getlist('comanage_groups'):
                    MembershipComanagePersonnel.objects.filter(
                        project=project.id,
                        comanage_groups=group.comanage_group.id
                    ).delete()
                    group.delete()
            for group_pk in form.data.getlist('comanage_groups'):
                if not MembershipComanageMemberActive.objects.filter(project=project.id,
                                                                     comanage_group=group_pk).exists():
                    MembershipComanageMemberActive.objects.create(
                        project=project,
                        comanage_group=ComanageMemberActive.objects.get(id=group_pk)
                    )
                    personnel = personnel_by_comanage_group(ComanageMemberActive.objects.get(id=group_pk).cn)
                    for person in personnel:
                        if not MembershipComanagePersonnel.objects.filter(
                                person=person,
                                project=project,
                                comanage_groups=ComanageMemberActive.objects.get(id=group_pk)):
                            MembershipComanagePersonnel.objects.create(
                                person=person,
                                project=project,
                                comanage_admins=None,
                                comanage_groups=ComanageMemberActive.objects.get(id=group_pk)
                            )
            # datasets
            current_datasets = MembershipDatasets.objects.filter(project=project.id)
            for ds in current_datasets:
                if str(ds.dataset.id) not in form.data.getlist('datasets'):
                    MembershipDatasets.objects.filter(
                        project=project.id,
                        dataset=ds.dataset.id
                    ).delete()
            for ds_pk in form.data.getlist('datasets'):
                if not MembershipDatasets.objects.filter(project=project.id, dataset=ds_pk).exists():
                    MembershipDatasets.objects.create(
                        project=project,
                        dataset=Dataset.objects.get(id=ds_pk)
                    )

            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_edit.html', {'projects_page': 'active', 'form': form, 'project_uuid': uuid})


def project_delete(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    comanage_admins = ComanageAdmin.objects.filter(cn__contains=':admins', project=project).order_by('cn')
    comanage_groups = ComanageMemberActive.objects.filter(cn__contains=':active', project=project).order_by('cn')
    ds_list = MembershipDatasets.objects.values_list('dataset__uuid').filter(project__uuid=uuid)
    ds_objs = Dataset.objects.filter(uuid__in=ds_list).order_by('name')
    wf_list = MembershipWorkflow.objects.values_list('workflow__uuid').filter(project__uuid=project.uuid)
    wf_objs = WorkflowNeo4j.objects.filter(uuid__in=wf_list).order_by('name')
    if request.method == "POST":
        pr_wf_list = MembershipWorkflow.objects.values_list('workflow__uuid').filter(
            project=project)
        pr_wf_objs = WorkflowNeo4j.objects.filter(uuid__in=pr_wf_list)
        for wf in pr_wf_objs:
            delete_workflow_from_uuid(workflow_uuid=str(wf.uuid))
            wf.delete()
        MembershipComanageAdmin.objects.filter(project=project.id).delete()
        MembershipComanageMemberActive.objects.filter(project=project.id).delete()
        project.delete()
        return project_list(request)
    return render(request, 'project_delete.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_admins': comanage_admins,
        'comanage_groups': comanage_groups,
        'datasets': ds_objs,
        'workflows': wf_objs,
    })
