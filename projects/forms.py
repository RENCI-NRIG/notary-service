from operator import itemgetter

from django import forms

from comanage.ldap import get_comanage_project_names
from datasets.models import Dataset
from infrastructure.models import Infrastructure
from .models import Project


class ProjectCreateForm(forms.ModelForm):
    comanage_projects = get_comanage_project_names()
    project_choices = ()
    for project in comanage_projects:
        project_choices += ((project, project),)

    project = forms.ChoiceField(
        choices=sorted(project_choices, key=itemgetter(1)),
        widget=forms.Select,
        label='COmanage Project',
        required=True
    )

    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60}),
        required=False
    )

    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 6, 'cols': 60}),
        required=False
    )

    class Meta:
        model = Project
        fields = (
            'project',
            'name',
            'description',
        )


class ProjectEditForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60})
    )
    datasets = forms.ModelMultipleChoiceField(
        queryset=Dataset.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label="Datasets",
        required=False
    )
    infrastructure = forms.ModelMultipleChoiceField(
        queryset=Infrastructure.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label="Infrastructure",
        required=False
    )

    class Meta:
        model = Project
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
        }
        fields = (
            'name',
            'description',
            'datasets',
            'infrastructure',
        )
