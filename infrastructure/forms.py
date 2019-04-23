from django import forms

from .models import Infrastructure


class InfrastructureForm(forms.ModelForm):
    name = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60})
    )
    affiliation = forms.CharField(
        widget=forms.TextInput(attrs={'size': 60}),
        disabled=True
    )

    class Meta:
        model = Infrastructure
        widgets = {
            'description': forms.Textarea(attrs={'rows': 6, 'cols': 60}),
        }
        fields = (
            'name',
            'description',
            'affiliation',
        )
