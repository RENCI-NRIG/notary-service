import os
from itertools import chain

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models import Q
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from comanage.comanage_api import create_co_person_role, remove_co_person_role, remove_co_cou
from datasets.models import Dataset, NSTemplate
from infrastructure.models import Infrastructure
from nsmessages.nsmessages import join_project_request, role_added_to_project, role_removed_from_project
from users.models import Affiliation
from users.models import ComanageCou
from users.models import NotaryServiceUser
from workflows import views as wf_views
from workflows.models import WorkflowNeo4j
from .forms import ProjectCreateForm, ProjectUpdateStaffForm, ProjectUpdatePiForm, \
    ProjectUpdateAdminForm, ProjectUpdateInfrastructureForm, ProjectUpdateDatasetForm
from .models import Project, MembershipProjectWorkflow
from .projects import create_new_project
from .workflows import create_base_project_workflows, generate_neo4j_user_workflow_status


@login_required()
def projects(request):
    """
    Display list of projects based on user role
    :param request:
    :return:
    """
    if request.method == "POST":
        if request.user.is_ig():
            if request.POST.get("ig-self-assign-project"):
                ns_project = Project.objects.filter(
                    uuid=request.POST.get("project_uuid")
                ).first()
                if ns_project:
                    ns_project.project_igs.add(request.user)
                    ns_project.save()
                    role_added_to_project(request=request, user=request.user,
                                          project=ns_project, role='Institutional Governance')
            if request.POST.get("ig-self-unassign-project"):
                ns_project = Project.objects.filter(
                    uuid=request.POST.get("project_uuid")
                ).first()
                if ns_project:
                    ns_project.project_igs.remove(request.user)
                    ns_project.save()
                    role_removed_from_project(request=request, user=request.user,
                                              project=ns_project, role='Institutional Governance')
        if request.POST.get("join-project-request"):
            ns_project = Project.objects.filter(
                uuid=request.POST.get("project_uuid")
            ).first()
            join_project_request(request=request, project=ns_project)
            messages.success(request, '[INFO] Request to join Project "{0}" has been sent'.format(ns_project.name))

    my_projects = Project.objects.filter(
        Q(created_by=request.user.email) |
        Q(comanage_pi_admins__in=[request.user]) |
        Q(comanage_pi_members__in=[request.user]) |
        Q(comanage_staff__in=[request.user]) |
        Q(project_igs__in=[request.user]) |
        Q(datasets__created_by__in=[request.user]) |
        Q(infrastructure__created_by__in=[request.user])
    ).order_by('name').distinct()
    other_projects = Project.objects.all().difference(my_projects).order_by('name')
    return render(request, 'projects.html',
                  {'my_projects': my_projects,
                   'other_projects': other_projects,
                   'projects_page': 'active'})


def project_validate(request, project_uuid: str, user: NotaryServiceUser):
    """
    Validate project components
    :param ds_objs:
    :param show_uuid:
    :param project_uuid:
    :param user:
    :return:
    """
    # TODO - be more rigorous in what it means to be "valid"
    ns_project = Project.objects.filter(uuid=project_uuid).first()
    if ns_project:
        if not ns_project.affiliation.all():
            messages.error(request, '[WARNING] must assign PI or STAFF members first ...')
            return False, None
        dsets = ns_project.datasets.all()
        if dsets:
            for ds in dsets:
                if not ds.is_valid:
                    messages.error(request, 'Dataset (' + str(ds.description)[:34] + '..) is not validated')
                    return False, None
        else:
            messages.error(request, '[WARNING] Datasets have not been assigned ...')
            return False, None
        try:
            if not ns_project.infrastructure.is_valid:
                messages.error(request, 'Infrastructure (' + ns_project.infrastructure.name + ') is not validated')
                return False, None
        except Exception as e:
            print(e)
            messages.error(request, '[WARNING] Infrastructure in not assigned ...')
            return False, None

        create_base_project_workflows(project_uuid, user)
    else:
        return False, 'Project ' + str(project_uuid) + ' is not found ...'

    return True, None


@login_required()
def project_detail(request, uuid):
    """
    Show project details based on user role
    :param request:
    :param uuid:
    :return:
    """
    project = get_object_or_404(Project, uuid=uuid)
    pi_admins = project.comanage_pi_admins.all().order_by('display_name')
    pi_members = project.comanage_pi_members.all().order_by('display_name')
    staff = project.comanage_staff.all().order_by('display_name')
    igs = project.project_igs.all().order_by('display_name')
    datasets = project.datasets.all()
    dso = [u.owner for u in datasets]
    infrastructure = project.infrastructure
    if infrastructure:
        ifo = [infrastructure.owner]
    else:
        ifo = []
    workflows = project.workflows.all()

    aff_set = list(chain(pi_members, staff))
    if [True for x in aff_set if request.user.id == x.id]:
        is_member = True
    else:
        is_member = False

    affiliation_orig = project.affiliation.all().order_by('co_person_id')
    co_person_ids = list(set([x.co_person_id for x in aff_set]))
    affiliation = Affiliation.objects.filter(
        co_person_id__in=co_person_ids
    ).order_by('co_person_id')
    affiliation_added = list(set(affiliation).difference(set(affiliation_orig)))
    affiliation_removed = list(set(affiliation_orig).difference(set(affiliation)))
    for a in affiliation_added:
        project.affiliation.add(a)
    for a in affiliation_removed:
        project.affiliation.remove(a)
    project.save()
    affiliations = project.affiliation.all().order_by('name').values('name').annotate(n=models.Count('pk'))
    project_error = None
    if request.method == "POST":
        if request.POST.get("validate"):
            project.is_valid, project_error = project_validate(request, project_uuid=project.uuid, user=request.user)
        if request.POST.get("clear-project-datasets"):
            # delete workflows
            for workflow in workflows:
                project.workflows.remove(workflow)
                workflow.delete()
            # remove datasets / infrastructure
            for dataset in datasets:
                project.datasets.remove(dataset)
            project.is_valid = False
            project.save()
            return redirect('project_detail', uuid=project.uuid)
    generate_neo4j_user_workflow_status(project, request.user)
    project.save()

    # print('### Project Workflows ###')
    # for wf in workflows:
    #     print('-', wf.uuid, '|', wf.affiliation.name, '|', wf.name)

    return render(request, 'project_detail.html', {
        'projects_page': 'active',
        'project': project,
        'affiliations': affiliations,
        'project_pi_admins': pi_admins,
        'project_pi_members': pi_members,
        'project_staff': staff,
        'datasets': datasets,
        'dataset_owners': dso,
        'project_error': project_error,
        'workflows': workflows,
        'infrastructure': infrastructure,
        'infrastructure_owner': ifo,
        'institutional_governance': igs,
        'is_member': is_member
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
        project_obj.workflows.add(workflow)
        project_obj.save()
        MembershipProjectWorkflow.objects.create(
            project=project_obj,
            dataset=dataset_obj,
            template=template_obj,
            workflow=workflow,
            is_generated=True,
        )


def project_new(request):
    """
    Create a new project based on existing COmanage groups
    :param request:
    :return:
    """
    if request.method == "POST":
        form = ProjectCreateForm(request.POST)
        if form.is_valid():
            project_name = form.cleaned_data['name']
            project_uuid = create_new_project(
                request,
                project_name=project_name,
                project_description=form.cleaned_data['description'],
                is_public=form.cleaned_data['is_public']
            )
            messages.success(request, '[INFO] Project {0} has been created'.format(project_name))
            return redirect('project_detail', uuid=project_uuid)
    else:
        form = ProjectCreateForm()
    return render(request, 'project_new.html', {'projects_page': 'active', 'form': form})


@login_required()
def project_edit(request, uuid):
    """
    Edit existing project - allow PI_ADMIN to add datasets and infrastructure to projects
    :param request:
    :param uuid:
    :return:
    """
    project = get_object_or_404(Project, uuid=uuid)
    project_pi_admins = project.comanage_pi_admins.all()
    if request.method == "POST":
        form = ProjectCreateForm(request.POST, instance=project)
        if form.is_valid():
            project.name = form.cleaned_data['name']
            project.description = form.cleaned_data['description']
            project.is_public = form.cleaned_data['is_public']
            project.modified_by = request.user.email
            project.is_valid = False
            project.save()
            messages.success(request, '[INFO] Project {0} has been updated'.format(project.name))
            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectCreateForm(instance=project)
    return render(request, 'project_edit.html', {'projects_page': 'active', 'form': form, 'project': project,
                                                 'project_pi_admins': project_pi_admins})


@login_required()
def project_delete(request, uuid):
    """
    Delete existing project and database table relationships
    :param request:
    :param uuid:
    :return:
    """
    project = get_object_or_404(Project, uuid=uuid)
    affiliations = project.affiliation.all().order_by('name').distinct('name')
    comanage_staff = project.comanage_staff.all().order_by('display_name')
    comanage_pi_members = project.comanage_pi_members.all().order_by('display_name')
    comanage_pi_admins = project.comanage_pi_admins.all().order_by('display_name')
    igs = project.project_igs.all().order_by('display_name')
    datasets = project.datasets.all().order_by('name')
    workflows = project.workflows.all().order_by('affiliation', 'name')
    if request.method == "POST":
        # delete workflows
        for workflow in workflows:
            project.workflows.remove(workflow)
            workflow.delete()
        # remove datasets / infrastructure
        for dataset in datasets:
            project.datasets.remove(dataset)
        if project.infrastructure:
            project.infrastructure = None
        # remove personnel
        staff_cou = ComanageCou.objects.filter(name=str(project.uuid) + os.getenv('COU_FLAG_STAFF')).first()
        if staff_cou:
            for staff in comanage_staff:
                rm_role = remove_co_person_role(co_person_id=staff.co_person_id, co_cou_id=staff_cou.co_cou_id)
                if rm_role:
                    project.comanage_staff.remove(staff)
        pi_member_cou = ComanageCou.objects.filter(name=str(project.uuid) + os.getenv('COU_FLAG_PI_MEMBER')).first()
        if pi_member_cou:
            for pi_member in comanage_pi_members:
                rm_role = remove_co_person_role(co_person_id=pi_member.co_person_id, co_cou_id=pi_member_cou.co_cou_id)
                if rm_role:
                    project.comanage_staff.remove(pi_member)
        pi_admin_cou = ComanageCou.objects.filter(name=str(project.uuid) + os.getenv('COU_FLAG_PI_ADMIN')).first()
        if pi_admin_cou:
            for pi_admin in comanage_pi_admins:
                rm_role = remove_co_person_role(co_person_id=pi_admin.co_person_id, co_cou_id=pi_admin_cou.co_cou_id)
                if rm_role:
                    project.comanage_staff.remove(pi_admin)
        # remove IGs
        for ig in igs:
            project.project_igs.remove(ig)
        # remove affiliations
        for aff in affiliations:
            project.affiliation.remove(aff)
        # delete project
        if remove_co_cou(staff_cou) and remove_co_cou(pi_member_cou) and remove_co_cou(pi_admin_cou):
            messages.success(
                request,
                '[INFO] Project "{0}" has been deleted'.format(project.name))
            project.delete()
        else:
            messages.error(
                request,
                '[ERROR] Failed to delete Project "{0}" ...'.format(project.name))
        return redirect('projects')

    return render(request, 'project_delete.html', {
        'projects_page': 'active',
        'project': project,
        'affiliations': affiliations,
        'project_pi_admins': comanage_pi_admins,
        'project_pi_members': comanage_pi_members,
        'project_staff': comanage_staff,
        'datasets': datasets,
        'workflows': workflows,
    })


@login_required()
def project_update_staff(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    pi_admins = project.comanage_pi_admins.all()
    pi_members = project.comanage_pi_members.all()
    comanage_staff_orig = list(project.comanage_staff.all())

    if request.method == "POST":
        form = ProjectUpdateStaffForm(request.POST, instance=project, request=request)
        if form.is_valid():
            comanage_staff = list(form.cleaned_data.get('comanage_staff'))
            comanage_staff_added = list(set(comanage_staff).difference(set(comanage_staff_orig)))
            comanage_staff_removed = list(set(comanage_staff_orig).difference(set(comanage_staff)))
            co_cou = ComanageCou.objects.filter(name=str(uuid) + os.getenv('COU_FLAG_STAFF')).first()
            # update staff
            for staff in comanage_staff_added:
                # create co_person role and add ns_role
                if create_co_person_role(co_person_id=staff.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # add user to comanage_staff
                    project.comanage_staff.add(staff)
                    role_added_to_project(request=request, user=staff, project=project, role='Staff')
                    messages.success(
                        request,
                        '[INFO] "{0}" added as STAFF to project "{1}"'.format(staff.display_name, project.name))
            for staff in comanage_staff_removed:
                # remove co_person role and add ns_role
                if remove_co_person_role(co_person_id=staff.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # remove user from comanage_staff
                    project.comanage_staff.remove(staff)
                    role_removed_from_project(request=request, user=staff, project=project, role='Staff')
                    messages.success(
                        request,
                        '[INFO] "{0}" removed as STAFF from project "{1}:'.format(staff.display_name, project.name))
            project.is_valid = False
            project.save()
            return redirect('project_detail', uuid=uuid)
    else:
        form = ProjectUpdateStaffForm(instance=project, request=request)

    return render(request, 'project_update_staff.html', {
        'form': form,
        'projects_page': 'active',
        'project': project,
        'project_pi_admins': pi_admins,
        'project_pi_members': pi_members
    })


@login_required()
def project_update_pi(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    pi_admins = project.comanage_pi_admins.all()
    pi_members = project.comanage_pi_members.all()
    comanage_pi_members_orig = list(project.comanage_pi_members.all())

    if request.method == "POST":
        form = ProjectUpdatePiForm(request.POST, instance=project, request=request)
        if form.is_valid():
            comanage_pi_members = list(form.cleaned_data.get('comanage_pi_members'))
            comanage_pi_members_added = list(set(comanage_pi_members).difference(set(comanage_pi_members_orig)))
            comanage_pi_members_removed = list(set(comanage_pi_members_orig).difference(set(comanage_pi_members)))
            co_cou = ComanageCou.objects.filter(name=str(uuid) + os.getenv('COU_FLAG_PI_MEMBER')).first()
            # update staff
            for pi_member in comanage_pi_members_added:
                # create co_person role and add ns_role
                if create_co_person_role(co_person_id=pi_member.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # add user to comanage_staff
                    project.comanage_pi_members.add(pi_member)
                    role_added_to_project(request=request, user=pi_member, project=project, role='PI or Co-PI')
                    messages.success(
                        request,
                        '[INFO] "{0}" added as PI to project "{1}"'.format(pi_member.display_name, project.name))
            for pi_member in comanage_pi_members_removed:
                # remove co_person role and add ns_role
                if remove_co_person_role(co_person_id=pi_member.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # remove user from comanage_staff
                    project.comanage_pi_members.remove(pi_member)
                    role_removed_from_project(request=request, user=pi_member, project=project, role='PI or Co-PI')
                    messages.success(
                        request,
                        '[INFO] "{0}" removed as PI from project "{1}:'.format(pi_member.display_name, project.name))
            project.is_valid = False
            project.save()
            return redirect('project_detail', uuid=uuid)
    else:
        form = ProjectUpdatePiForm(instance=project, request=request)

    return render(request, 'project_update_pi.html', {
        'form': form,
        'projects_page': 'active',
        'project': project,
        'project_pi_admins': pi_admins,
        'project_pi_members': pi_members
    })


@login_required()
def project_update_admin(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    pi_admins = project.comanage_pi_admins.all()
    pi_members = project.comanage_pi_members.all()
    comanage_pi_admins_orig = list(project.comanage_pi_admins.all())

    if request.method == "POST":
        form = ProjectUpdateAdminForm(request.POST, instance=project)
        if form.is_valid():
            comanage_pi_admins = list(form.cleaned_data.get('comanage_pi_admins'))
            comanage_pi_admins_added = list(set(comanage_pi_admins).difference(set(comanage_pi_admins_orig)))
            comanage_pi_admins_removed = list(set(comanage_pi_admins_orig).difference(set(comanage_pi_admins)))
            co_cou = ComanageCou.objects.filter(name=str(uuid) + os.getenv('COU_FLAG_PI_ADMIN')).first()
            # update staff
            for pi_admin in comanage_pi_admins_added:
                # create co_person role and add ns_role
                if create_co_person_role(co_person_id=pi_admin.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # add user to comanage_staff
                    project.comanage_pi_admins.add(pi_admin)
                    role_added_to_project(request=request, user=pi_admin, project=project, role='Project Manager')
                    messages.success(
                        request,
                        '[INFO] "{0}" added as MANAGER to project "{1}"'.format(pi_admin.display_name, project.name))
            for pi_admin in comanage_pi_admins_removed:
                # remove co_person role and add ns_role
                if remove_co_person_role(co_person_id=pi_admin.co_person_id, co_cou_id=co_cou.co_cou_id):
                    # remove user from comanage_staff
                    project.comanage_pi_admins.remove(pi_admin)
                    role_removed_from_project(request=request, user=pi_admin, project=project, role='Project Manager')
                    messages.success(
                        request,
                        '[INFO] "{0}" removed as MANAGER from project "{1}:'.format(pi_admin.display_name,
                                                                                    project.name))
            project.is_valid = False
            project.save()
            return redirect('project_detail', uuid=uuid)
    else:
        form = ProjectUpdateAdminForm(instance=project)

    return render(request, 'project_update_admin.html', {
        'form': form,
        'projects_page': 'active',
        'project': project,
        'project_pi_admins': pi_admins,
        'project_pi_members': pi_members
    })


@login_required()
def project_update_infra(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    project_pi_admins = project.comanage_pi_admins.all()
    project_pi_members = project.comanage_pi_members.all()
    infra = project.infrastructure
    if request.method == "POST":
        form = ProjectUpdateInfrastructureForm(request.POST, instance=project)
        if form.is_valid():
            infra_choice = form.cleaned_data['infrastructure']
            # print(infra_choice)
            if infra_choice is not None:
                project.infrastructure = Infrastructure.objects.filter(id=infra_choice.id).first()
                project.save()
                role_added_to_project(request=request, user=project.infrastructure.owner,
                                      project=project, role='Infrastructure Provider')
                if infra:
                    if infra.id != project.infrastructure.id:
                        role_removed_from_project(request=request, user=infra.owner,
                                                  project=project, role='Infrastructure Provider')
                messages.success(request, '[INFO] Infrastructure "{0}" added to Project "{1}"'.format(infra_choice,
                                                                                                      project.name))
            else:
                project.save()
                messages.success(request, '[INFO] No Infrastructure assigned to Project "{0}"'.format(project.name))
            project.is_valid = False
            project.save()
            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectUpdateInfrastructureForm(instance=project)
    return render(request, 'project_update_infrastructure.html',
                  {'projects_page': 'active', 'form': form,
                   'project_pi_admins': project_pi_admins, 'project_pi_members': project_pi_members,
                   'project': project})


@login_required()
def project_update_dataset(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    project_pi_admins = project.comanage_pi_admins.all()
    project_pi_members = project.comanage_pi_members.all()
    dataset_choices_orig = list(project.datasets.all())
    if request.method == "POST":
        form = ProjectUpdateDatasetForm(request.POST, instance=project)
        if form.is_valid():
            dataset_choices = list(form.cleaned_data['datasets'])
            dataset_choices_added = list(set(dataset_choices).difference(set(dataset_choices_orig)))
            dataset_choices_removed = list(set(dataset_choices_orig).difference(set(dataset_choices)))
            for dataset in dataset_choices_added:
                project.datasets.add(dataset)
                role_added_to_project(request=request, user=dataset.owner, project=project, role='Dataset Provider')
                messages.success(request, '[INFO] Dataset "{0}" added to Project "{1}"'.format(dataset,
                                                                                               project.name))
            for dataset in dataset_choices_removed:
                project.datasets.remove(dataset)
                role_removed_from_project(request=request, user=dataset.owner, project=project, role='Dataset Provider')
                messages.success(request, '[INFO] Removed Dataset "{0}" from Project "{1}"'.format(dataset,
                                                                                                   project.name))
            project.save()
        else:
            project.save()
            messages.success(request, '[INFO] No Dataset assigned to Project "{0}"'.format(project.name))
            project.is_valid = False
            project.save()
        return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectUpdateDatasetForm(instance=project)
    return render(request, 'project_update_dataset.html',
                  {'projects_page': 'active', 'form': form,
                   'project_pi_admins': project_pi_admins, 'project_pi_members': project_pi_members,
                   'project': project})
