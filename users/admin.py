# from django.contrib import admin
# from django.contrib.admin import ModelAdmin
# from django.contrib.auth.admin import UserAdmin
#
# from users.models import Affiliation
# from .forms import UserCreationForm, UserChangeForm, AffiliationChangeForm, AffiliationCreationForm
# from .models import NotaryServiceUser
#
#
# class NotaryServiceUserAdmin(UserAdmin):
#     add_form = UserCreationForm
#     form = UserChangeForm
#     model = NotaryServiceUser
#     list_display = ['username', 'email', 'first_name', 'last_name', 'idp']
#
#
# admin.site.register(NotaryServiceUser, NotaryServiceUserAdmin)
#
#
# class AffiliationAdmin(ModelAdmin):
#     add_form = AffiliationCreationForm
#     form = AffiliationChangeForm
#     model = Affiliation
#     list_display = ['display_name', 'idp_name', 'idp', 'uuid']
#
#
# admin.site.register(Affiliation, AffiliationAdmin)
