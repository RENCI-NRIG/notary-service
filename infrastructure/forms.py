from django import forms

from .models import Infrastructure
from users.models import Affiliation


class InfrastructureCreateForm(forms.ModelForm):
    class Meta:
        model = Infrastructure
        fields = [
            'name',
            'description'
        ]


class InfrastructureEditForm(forms.ModelForm):
    class Meta:
        model = Infrastructure
        fields = [
            'name',
            'description'
        ]


# class InfrastructureForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         user = kwargs.pop('user')
#         super(InfrastructureForm, self).__init__(*args, **kwargs)
#         self.fields['affiliation'] = forms.ModelChoiceField(
#             queryset=Affiliation.objects.all().order_by('display_name'),
#             label='Organizational Affiliation',
#             empty_label=None,
#         )
#
#     name = forms.CharField(
#         widget=forms.TextInput(attrs={'size': 60})
#     )
#     affiliation = forms.CharField(
#         widget=forms.TextInput(attrs={'size': 60}),
#         disabled=True
#     )
#
#     class Meta:
#         model = Infrastructure
#         widgets = {
#             'description': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
#         }
#         fields = (
#             'name',
#             'description',
#             'affiliation',
#         )
