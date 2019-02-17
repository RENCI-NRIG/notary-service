from django.shortcuts import render, get_object_or_404

from comanage.models import IsMemberOf, LdapOther, NotaryServiceUser
from .forms import UserPreferences


def index(request):
    context = {"index_page": "active"}
    return render(request, 'index.html', context)


def about(request):
    context = {"about_page": "active"}
    return render(request, 'about.html', context)


def contact(request):
    context = {"contact_page": "active"}
    return render(request, 'contact.html', context)


def search(request):
    context = {"search_page": "active"}
    return render(request, 'search.html', context)


def login(request):
    context = {"login_page": "active"}
    return render(request, 'login.html', context)


def faq(request):
    context = {"faq_page": "active"}
    return render(request, 'faq.html', context)


def profile(request):
    if request.user.is_authenticated:
        user = get_object_or_404(NotaryServiceUser, id=request.user.id)
        ismemberof = IsMemberOf.objects.filter(
            membershipismemberof__user_id=request.user.id).order_by('value')
        ldapother = LdapOther.objects.filter(
            membershipldapother__user_id=request.user.id).order_by('attribute', 'value')
        if request.method == "POST":
            form = UserPreferences(request.POST, instance=user)
            if form.is_valid():
                user.show_uuid = form.data.get('show_uuid')
                user.save()
        else:
            form = UserPreferences(instance=user)
        return render(request, 'profile.html',
                      {'profile_page': 'active',
                       'isMemberOf': ismemberof,
                       'LDAPOther': ldapother,
                       'form': form})
    else:
        return render(request, 'profile.html', {'profile_page': 'active'})
