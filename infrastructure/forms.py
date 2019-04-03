from django import forms

from .models import Infrastructure


class InfrastructureForm(forms.ModelForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'size': 60}))
    affiliation = forms.CharField(widget=forms.TextInput(attrs={'size': 60}))

    class Meta:
        model = Infrastructure
        fields = (
            'name',
            'description',
            'affiliation',
        )
