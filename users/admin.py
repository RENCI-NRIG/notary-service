from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import UserCreationForm, UserChangeForm
from .models import NotaryServiceUser


class NotaryServiceUserAdmin(UserAdmin):
    add_form = UserCreationForm
    form = UserChangeForm
    model = NotaryServiceUser
    list_display = ['username', 'email', 'first_name', 'last_name', 'idp']


admin.site.register(NotaryServiceUser, NotaryServiceUserAdmin)
