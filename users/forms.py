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
