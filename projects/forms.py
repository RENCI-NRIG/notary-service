from django import forms
from .models import Project, ComanageGroup


class ProjectForm(forms.ModelForm):
    admin_groups = forms.ModelMultipleChoiceField(
        queryset=ComanageGroup.objects.filter(cn__contains=':admins', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Administrative groups'
    )
    comanage_groups = forms.ModelMultipleChoiceField(
        queryset=ComanageGroup.objects.filter(cn__contains=':active', active=True).order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Membership groups',
    )

    class Meta:
        model = Project
        fields = (
            'name',
            'description',
            'admin_groups',
            'comanage_groups',
        )


