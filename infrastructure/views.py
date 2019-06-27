from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from projects.models import MembershipInfrastructure
from projects.models import Project
from .forms import InfrastructureForm
from .models import Infrastructure
from users.models import Affiliation


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


def infrastructure_list(request):
    infra_objs = Infrastructure.objects.filter(created_date__lte=timezone.now()).order_by('name')
    return infra_objs


def infrastructure(request):
    if request.user.is_authenticated:
        infra_objs = infrastructure_list(request)
        return render(request, 'infrastructure.html', {"infrastructure_page": "active", "infra_objs": infra_objs})
    else:
        return render(request, 'infrastructure.html', {"infrastructure_page": "active"})


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


def infrastructure_new(request):
    if request.method == "POST":
        form = InfrastructureForm(
            request.POST,
            user=request.user,
            initial={'affiliation': Affiliation.objects.get(idp_name=request.user.idp_name).id}
        )
        if form.is_valid():
            infra = form.save(commit=False)
            infra.owner = request.user
            infra.created_by = request.user
            infra.modified_by = request.user
            infra.modified_date = timezone.now()
            infra.affiliation = str(Affiliation.objects.get(id=form['affiliation'].value()).uuid)
            infra.save()
            return redirect('infrastructure_detail', uuid=infra.uuid)
    else:
        form = InfrastructureForm(
            user=request.user,
            initial={'affiliation': Affiliation.objects.get(idp_name=request.user.idp_name).id},
        )
    return render(request, 'infrastructure_new.html', {'infrastructure_page': 'active', 'form': form})


def infrastructure_edit(request, uuid):
    infra = get_object_or_404(Infrastructure, uuid=uuid)
    if request.method == "POST":
        form = InfrastructureForm(
            request.POST,
            instance=infra,
            user=request.user,
            initial={'affiliation': Affiliation.objects.get(uuid=infra.affiliation).id},
        )
        if form.is_valid():
            infra = form.save(commit=False)
            infra.modified_by = request.user
            infra.modified_date = timezone.now()
            infra.is_valid = False
            infra.affiliation = str(Affiliation.objects.get(id=form['affiliation'].value()).uuid)
            infra.save()
            return redirect('infrastructure_detail', uuid=infra.uuid)
    else:
        form = InfrastructureForm(
            instance=infra,
            user=request.user,
            initial={'affiliation': Affiliation.objects.get(uuid=infra.affiliation).id},
        )
    return render(request, 'infrastructure_edit.html', {'infrastructure_page': 'active', 'form': form, 'uuid': uuid})


def infrastructure_delete(request, uuid):
    infra = get_object_or_404(Infrastructure, uuid=uuid)
    used_by = infrastructure_in_use(uuid)
    if request.method == "POST":
        infra.delete()
        return redirect('infrastructure')
    return render(request, 'infrastructure_delete.html', {
        'infrastructure_page': 'active',
        'infrastructure': infra,
        'used_by': used_by,
    })
