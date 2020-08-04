from operator import itemgetter

from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

from users.models import Affiliation
from .models import NotaryServiceUser


class UserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = NotaryServiceUser
        fields = ('username', 'email', 'first_name', 'last_name')


class UserChangeForm(UserChangeForm):
    class Meta:
        model = NotaryServiceUser
        fields = ('username', 'email', 'first_name', 'last_name')


class UserPreferences(forms.ModelForm):

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        role_choices = ()
        for role in user.roles.filter(notaryserviceuser=user):
            role_choices += ((role.id, role.get_id_display()),)
        super(UserPreferences, self).__init__(*args, **kwargs)
        self.fields['role'] = forms.ChoiceField(
            choices=sorted(role_choices, key=itemgetter(1)),
            widget=forms.RadioSelect(attrs={'class': 'profile-radios'}),
            label='Change user role',
            required=False
        )

    VIEW_CHOICE = (
        (True, 'Show UUIDs'),
        (False, 'Show Description'),
    )

    show_uuid = forms.ChoiceField(
        choices=VIEW_CHOICE,
        widget=forms.RadioSelect(attrs={'class': 'profile-radios'}),
        label='Change URL rendering',
        required=False,
    )

    class Meta:
        model = NotaryServiceUser
        fields = (
            'role',
            'show_uuid',
        )

class AffiliationCreationForm(forms.ModelForm):
    class Meta:
        model = Affiliation
        fields = ('display_name', 'idp_name', 'idp')


class AffiliationChangeForm(forms.ModelForm):
    class Meta:
        model = Affiliation
        fields = ('display_name', 'idp_name', 'idp')


class CILogonCertificateForm(forms.Form):
    """
    Certificate information form
    :var authorization_response - URL returned by CILogon authorization check
    :var p12_password - User entered password for p12 certificate generation
    """
    authorization_response = forms.CharField(max_length=1024)
    p12_password = forms.CharField(widget=forms.PasswordInput(), max_length=255)
