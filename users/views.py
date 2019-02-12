from django.shortcuts import render

from comanage.views import ldap_attributes


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


def profile(request):
    context = {"profile_page": "active"}
    if request.user.is_authenticated:
        return ldap_attributes(request)
    else:
        return render(request, 'profile.html', context)


def faq(request):
    context = {"faq_page": "active"}
    return render(request, 'faq.html', context)
