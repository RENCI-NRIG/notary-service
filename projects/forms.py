from django import forms

from datasets.models import Dataset
from infrastructure.models import Infrastructure
from .models import Project, ComanagePIAdmin, ComanageStaff


class ProjectForm(forms.ModelForm):
    comanage_pi_admins = forms.ModelMultipleChoiceField(
        queryset=ComanagePIAdmin.objects.filter(cn__contains='-PI:admins', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Administrative groups'
    )
    comanage_staff = forms.ModelMultipleChoiceField(
        queryset=ComanageStaff.objects.filter(cn__contains='-STAFF:members:active', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Membership groups',
    )
    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label="Datasets",
    )
    infrastructure = forms.ModelMultipleChoiceField(
        queryset=Infrastructure.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label="Infrastructure",
    )

    class Meta:
        model = Project
        fields = (
            'name',
            'description',
            'comanage_pi_admins',
            'comanage_staff',
            'datasets',
            'infrastructure',
        )
