from uuid import UUID

from django import forms

from .models import NSTemplate, Dataset


class TemplateForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60})
    )
    type = forms.CharField(
        widget=forms.Select(
            choices=(
                ('research_approval', 'Research Approval'),
                ('infrastructure_approval', 'Infrastructure Approval'),
            )
        )
    )

    class Meta:
        model = NSTemplate
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 60})
        }
        fields = (
            'name',
            'description',
            'type',
            'safe_identifier_as_scid',
            'graphml_definition',
        )

    def clean(self):
        cleaned_data = super().clean()
        template_scid = cleaned_data.get("safe_identifier_as_scid")
        try:
            sha_hash, uuid = str(template_scid).split(':')
            if len(sha_hash) != 44:
                raise forms.ValidationError(
                    {'safe_identifier_as_scid': ["Improperly formatted SAFE SCID: Hash format"]}
                )
            ver = UUID(uuid).version
            if ver != 4:
                raise forms.ValidationError(
                    {'safe_identifier_as_scid': ["Improperly formatted SAFE SCID: UUID version"]}
                )
        except ValueError:
            raise forms.ValidationError({'safe_identifier_as_scid': ["Improperly formatted SAFE SCID"]})


class DatasetForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request')
        super(DatasetForm, self).__init__(*args, **kwargs)
        if self.request.user.is_nsadmin():
            self.fields['templates'].queryset = NSTemplate.objects.all().order_by('name')
        else:
            self.fields['templates'].queryset = NSTemplate.objects.filter(
                    created_by__in=[self.request.user]
                ).order_by('name')

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
        queryset=None,
        widget=forms.SelectMultiple(),
        label='Templates',
        required=False
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

    def clean(self):
        cleaned_data = super().clean()
        data_scid = cleaned_data.get("safe_identifier_as_scid")
        try:
            sha_hash, uuid = str(data_scid).split(':')
            if len(sha_hash) != 44:
                raise forms.ValidationError(
                    {'safe_identifier_as_scid': ["Improperly formatted SAFE SCID: Hash format"]}
                )
            ver = UUID(uuid).version
            if ver != 4:
                raise forms.ValidationError(
                    {'safe_identifier_as_scid': ["Improperly formatted SAFE SCID: UUID version"]}
                )
        except ValueError:
            raise forms.ValidationError({'safe_identifier_as_scid': ["Improperly formatted SAFE SCID"]})
