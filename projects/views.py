from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from .forms import ProjectForm
from .models import Project, MembershipComanage, ComanageGroup
from .projects import update_comanage_group


def projects(request):
    context = {"projects_page": "active"}
    if request.user.is_authenticated:
        return project_list(request)
    else:
        return render(request, 'projects.html', context)


def project_detail(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    comanage_groups = ComanageGroup.objects.filter(project=project).values()
    return render(request, 'project_detail.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_groups': comanage_groups
    })


def project_list(request):
    projects = Project.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return render(request, 'projects.html', {'projects_page': 'active', 'projects': projects})


def project_new(request):
    update_comanage_group()
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            project = form.save(commit=False)
            project.modified_date = timezone.now()
            project.save()
            for group_pk in form.data.getlist('comanage_groups'):
                if not MembershipComanage.objects.filter(project=project.id, comanage_group=group_pk).exists():
                    MembershipComanage.objects.create(
                        project=project,
                        comanage_group=ComanageGroup.objects.get(id=group_pk)
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
            current_groups = MembershipComanage.objects.filter(project=project.id)
            for group in current_groups:
                if str(group.comanage_group.id) not in form.data.getlist('comanage_groups'):
                    group.delete()
            for group_pk in form.data.getlist('comanage_groups'):
                if not MembershipComanage.objects.filter(project=project.id, comanage_group=group_pk).exists():
                    MembershipComanage.objects.create(
                        project=project,
                        comanage_group=ComanageGroup.objects.get(id=group_pk)
                    )
            return redirect('project_detail', uuid=project.uuid)
    else:
        form = ProjectForm(instance=project)
    return render(request, 'project_edit.html', {'projects_page': 'active', 'form': form})


def project_delete(request, uuid):
    project = get_object_or_404(Project, uuid=uuid)
    comanage_groups = ComanageGroup.objects.filter(project=project).values()
    if request.method == "POST":
        MembershipComanage.objects.filter(project=project.id).delete()
        project.delete()
    return render(request, 'project_delete.html', {
        'projects_page': 'active',
        'project': project,
        'comanage_groups': comanage_groups
    })
