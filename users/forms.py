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
        # print(role_choices)
        super(UserPreferences, self).__init__(*args, **kwargs)
        self.fields['role'] = forms.ChoiceField(
            choices=sorted(role_choices, key=itemgetter(1)),
            widget=forms.Select,
            label='User role',
            required=False
        )

    VIEW_CHOICE = (
        (True, 'Show UUIDs'),
        (False, 'Show Description'),
    )

    show_uuid = forms.ChoiceField(
        choices=VIEW_CHOICE,
        widget=forms.Select,
        label='URL rendering',
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
