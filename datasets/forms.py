from django import forms

from .models import NSTemplate, Dataset


class TemplateForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60})
    )

    class Meta:
        model = NSTemplate
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
        }
        fields = (
            'name',
            'description',
            'graphml_definition',
        )


class DatasetForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60})
    )
    dataset_identifier_as_url = forms.URLField(
        widget=forms.TextInput(attrs={'size': 60}),
        label='Presidio URL'
    )
    dataset_identifier_as_doi_or_meta = forms.URLField(
        widget=forms.TextInput(attrs={'size': 60}),
        label='DOI or metadata URL',
        required=False
    )
    safe_identifier_as_scid = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60}),
        label='SAFE SCID'
    )
    templates = forms.ModelMultipleChoiceField(
        queryset=NSTemplate.objects.order_by('name'),
        widget=forms.SelectMultiple(),
        label='Templates',
    )

    class Meta:
        model = Dataset
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
        }
        fields = (
            'name',
            'description',
            'dataset_identifier_as_url',
            'dataset_identifier_as_doi_or_meta',
            'safe_identifier_as_scid',
            'templates',
        )
