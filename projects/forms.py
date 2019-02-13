from django import forms
from .models import Project, ComanageAdmin, ComanageMemberActive
from datasets.models import Dataset


class ProjectForm(forms.ModelForm):
    comanage_admins = forms.ModelMultipleChoiceField(
        queryset=ComanageAdmin.objects.filter(cn__contains=':admins', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Administrative groups'
    )
    comanage_groups = forms.ModelMultipleChoiceField(
        queryset=ComanageMemberActive.objects.filter(cn__contains=':active', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Membership groups',
    )
    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label="Datasets",
    )

    class Meta:
        model = Project
        fields = (
            'name',
            'description',
            'comanage_admins',
            'comanage_groups',
            'datasets'
        )


