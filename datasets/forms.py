from django import forms

from .models import NSTemplate, Dataset


class TemplateForm(forms.ModelForm):
    class Meta:
        model = NSTemplate
        fields = (
            'name',
            'description',
            'graphml_definition',
        )


class DatasetForm(forms.ModelForm):
    templates = forms.ModelMultipleChoiceField(
        queryset=NSTemplate.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label='Templates',
    )

    class Meta:
        model = Dataset
        fields = (
            'name',
            'description',
            'dataset_identifier_as_url',
            'safe_identifier_as_scid',
            'templates'
        )
