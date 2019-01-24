from itertools import chain
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import ProjectForm
from .models import Project, ComanageMemberActive, ComanageAdmin, ComanagePersonnel, \
    MembershipComanageMemberActive, MembershipComanageAdmin, MembershipComanagePersonnel
from .projects import update_comanage_group, personnel_by_comanage_group, update_comanage_personnel


def projects(request):
    context = {"projects_page": "active"}
    if request.user.is_authenticated:
        return project_list(request)
    else:
        return render(request, 'projects.html', context)


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
    print(admin_group)
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
    return render(request, 'project_detail.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_admins': comanage_admins,
        'comanage_groups': comanage_groups,
        'admin_group': admin_group,
        'member_group': member_group,
    })


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
            project.modified_date = timezone.now()
            project.save()
            # admin groups
            for group_pk in form.data.getlist('comanage_admins'):
                print('ADMIN: ' + group_pk)
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
                print('MEMBER: ' + group_pk)
                if not MembershipComanageMemberActive.objects.filter(project=project.id, comanage_group=group_pk).exists():
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
                print('ADMIN: ' + group_pk)
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
                    MembershipComanagePersonnel.objects.filter(project=project.id,
                                                               comanage_groups=group.comanage_group.id).delete()
                    group.delete()
            for group_pk in form.data.getlist('comanage_groups'):
                print('MEMBER: ' + group_pk)
                if not MembershipComanageMemberActive.objects.filter(project=project.id, comanage_group=group_pk).exists():
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

            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_edit.html', {'projects_page': 'active', 'form': form})


def project_delete(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    comanage_admins = ComanageAdmin.objects.filter(cn__contains=':admins', project=project).order_by('cn')
    comanage_groups = ComanageMemberActive.objects.filter(cn__contains=':active', project=project).order_by('cn')
    if request.method == "POST":
        MembershipComanageAdmin.objects.filter(project=project.id).delete()
        project.delete()
        return project_list(request)
    return render(request, 'project_delete.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_admins': comanage_admins,
        'comanage_groups': comanage_groups,
    })
