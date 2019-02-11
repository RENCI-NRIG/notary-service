from django import forms
from .models import NSTemplate, MembershipNSTemplate


class TemplateForm(forms.ModelForm):

    class Meta:
        model = NSTemplate
        fields = (
            'name',
            'description',
            'graphml_definition',
        )

