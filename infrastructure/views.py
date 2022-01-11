from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from projects.models import MembershipInfrastructure
from users.models import Affiliation
from .forms import InfrastructureCreateForm, InfrastructureEditForm
from .models import Infrastructure


def infrastructure_validate(infra_uuid):
    return True, None


def infrastructure_in_use(infra_uuid):
    infra_list = MembershipInfrastructure.objects.values_list(
        'project__uuid',
    ).filter(
        infrastructure__uuid=infra_uuid,
    )
    infra_objs = Infrastructure.objects.filter(uuid__in=infra_list).order_by('name')
    return infra_objs


@login_required()
def infrastructure(request):
    my_infra = Infrastructure.objects.filter(
        created_by__in=[request.user]
    ).order_by('name').distinct()
    other_infra = Infrastructure.objects.all().difference(my_infra).order_by('name')

    return render(request, 'infrastructure.html', {
        'infrastructure_page': 'active', 'my_infrastructure': my_infra, 'other_infrastructure': other_infra
    })


@login_required()
def infrastructure_detail(request, uuid):
    infra = get_object_or_404(Infrastructure, uuid=uuid)
    if request.method == "POST":
        infra.is_valid, infrastructure_error = infrastructure_validate(str(infra.uuid))
        infra.save()
    else:
        infrastructure_error = None
    return render(request, 'infrastructure_detail.html', {
        'infrastructure_page': 'active',
        'infrastructure': infra,
        'infrastructure_error': infrastructure_error,
    })


@login_required()
def infrastructure_new(request):
    if request.method == "POST":
        form = InfrastructureCreateForm(request.POST)
        if form.is_valid():
            infra = Infrastructure()
            infra.name = form.cleaned_data['name']
            infra.description = form.cleaned_data['description']
            infra.owner = request.user
            infra.is_valid = False
            infra.created_by = request.user
            infra.created_date = timezone.now()
            infra.modified_by = request.user
            infra.modified_date = timezone.now()
            infra.affiliation = Affiliation.objects.filter(co_person_id=request.user.co_person_id).first()
            infra.save()
            messages.success(request, '[INFO] Infrastructure "{0}" has been created'.format(infra.name))
            return redirect('infrastructure_detail', uuid=infra.uuid)
    else:
        form = InfrastructureCreateForm()
    return render(request, 'infrastructure_new.html', {'infrastructure_page': 'active', 'form': form})


@login_required()
def infrastructure_edit(request, uuid):
    infra = get_object_or_404(Infrastructure, uuid=uuid)
    if request.method == "POST":
        form = InfrastructureEditForm(request.POST, instance=infra)
        if form.is_valid():
            infra.name = form.cleaned_data['name']
            infra.description = form.cleaned_data['description']
            infra.is_valid = False
            infra.modified_by = request.user
            infra.modified_date = timezone.now()
            infra.save()
            messages.success(request, '[INFO] Infrastructure "{0}" has been updated'.format(infra.name))
            return redirect('infrastructure_detail', uuid=infra.uuid)
    else:
        form = InfrastructureEditForm(instance=infra)
    return render(request, 'infrastructure_edit.html', {'infrastructure_page': 'active', 'form': form, 'infra': infra})


@login_required()
def infrastructure_delete(request, uuid):
    infra = get_object_or_404(Infrastructure, uuid=uuid)
    used_by = infrastructure_in_use(uuid)
    if request.method == "POST":
        messages.success(request, '[INFO] Infrastructure "{0}" has been removed'.format(infra.name))
        infra.delete()
        return redirect('infrastructure')
    return render(request, 'infrastructure_delete.html', {
        'infrastructure_page': 'active',
        'infrastructure': infra,
        'used_by': used_by,
    })
