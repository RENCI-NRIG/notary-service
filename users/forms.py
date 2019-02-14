from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm

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
            'show_uuid',
        )
