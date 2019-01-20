from django import forms
from .models import Project, ComanageGroup


class ProjectForm(forms.ModelForm):
    comanage_groups = forms.ModelMultipleChoiceField(
        queryset=ComanageGroup.objects.all().order_by('cn'),
        widget=forms.SelectMultiple(),
        label='Permissible groups',
    )

    class Meta:
        model = Project
        fields = (
            'name',
            'description',
            'comanage_groups',
        )


