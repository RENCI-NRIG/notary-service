import os

from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple

from users.models import NotaryServiceUser
from .models import Project
from infrastructure.models import Infrastructure
from datasets.models import Dataset


class ProjectCreateForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'is_public'
        ]


class ProjectEditForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = [
            'name',
            'description',
            'is_public'
        ]


class ProjectUpdateInfrastructureForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectUpdateInfrastructureForm, self).__init__(*args, **kwargs)
        self.fields['infrastructure'] = forms.ModelChoiceField(
            queryset=Infrastructure.objects.all().order_by('name'),
            required=False
        )

    class Meta:
        model = Project
        fields = [
            'infrastructure'
        ]


class ProjectUpdateDatasetForm(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        super(ProjectUpdateDatasetForm, self).__init__(*args, **kwargs)
        self.fields['datasets'] = forms.ModelMultipleChoiceField(
            queryset=Dataset.objects.all().order_by('name'),
            required=False
        )

    class Meta:
        model = Project
        fields = [
            'datasets'
        ]


class ProjectUpdateStaffForm(forms.ModelForm):
    comanage_staff = forms.ModelMultipleChoiceField(
        queryset=NotaryServiceUser.objects.filter(
            roles__co_cou__name=os.getenv('ROLE_IMPACT_USER')
        ).order_by('display_name'),
        widget=FilteredSelectMultiple("Staff", is_stacked=False),
        required=False
    )

    class Media:
        extend = False
        css = {
            'all': [
                'admin/css/widgets.css'
            ]
        }
        js = (
            'js/django_global.js',
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/prepopulate_init.js',
            'admin/js/prepopulate.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
            'admin/js/admin/RelatedObjectLookups.js',
        )

    class Meta:
        model = Project
        fields = [
            'comanage_staff'
        ]


class ProjectUpdatePiForm(forms.ModelForm):
    comanage_pi_members = forms.ModelMultipleChoiceField(
        queryset=NotaryServiceUser.objects.filter(
            roles__co_cou__name=os.getenv('ROLE_PI')
        ).order_by('display_name'),
        widget=FilteredSelectMultiple("Principal Investigators", is_stacked=False),
        required=False
    )

    class Media:
        extend = False
        css = {
            'all': [
                'admin/css/widgets.css'
            ]
        }
        js = (
            'js/django_global.js',
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/prepopulate_init.js',
            'admin/js/prepopulate.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
            'admin/js/admin/RelatedObjectLookups.js',
        )

    class Meta:
        model = Project
        fields = [
            'comanage_pi_members'
        ]


class ProjectUpdateAdminForm(forms.ModelForm):
    comanage_pi_admins = forms.ModelMultipleChoiceField(
        queryset=NotaryServiceUser.objects.filter(
            roles__co_cou__name=os.getenv('ROLE_PI')
        ).order_by('display_name'),
        widget=FilteredSelectMultiple("Administrators", is_stacked=False),
        required=False
    )

    class Media:
        extend = False
        css = {
            'all': [
                'admin/css/widgets.css'
            ]
        }
        js = (
            'js/django_global.js',
            'admin/js/jquery.init.js',
            'admin/js/core.js',
            'admin/js/prepopulate_init.js',
            'admin/js/prepopulate.js',
            'admin/js/SelectBox.js',
            'admin/js/SelectFilter2.js',
            'admin/js/admin/RelatedObjectLookups.js',
        )

    class Meta:
        model = Project
        fields = [
            'comanage_pi_admins'
        ]