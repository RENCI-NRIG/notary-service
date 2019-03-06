from django.shortcuts import render, get_object_or_404

from apache_kafka.models import Message
from apache_kafka.views import index_page_messages, check_for_new_messages
from comanage.models import IsMemberOf, LdapOther, NotaryServiceUser
from .forms import UserPreferences


def index(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            if request.POST.get("delete-message"):
                message = get_object_or_404(Message, uuid=request.POST.get('remove_message_uuid'))
                message.is_active = False
                message.save()
        return index_page_messages(request)
    else:
        return render(request, 'index.html', {'index_page': 'active'})


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
        form = UserPreferences(instance=user)
        if request.method == "POST":
            if request.POST.get("delete-message"):
                message = get_object_or_404(Message, uuid=request.POST.get('remove_message_uuid'))
                message.is_active = False
                message.save()
            if request.POST.get("update-preferences"):
                form = UserPreferences(request.POST, instance=user)
                if form.is_valid():
                    user.show_uuid = form.data.get('show_uuid')
                    user.save()
                elif request.POST.get("check-messages"):
                    check_for_new_messages(str(request.user.uuid))
        ns_messages = Message.objects.filter(
            kafka_topic=str(request.user.uuid),
            is_active=True).order_by('-created_date')[:5]
        return render(request, 'profile.html',
                      {'profile_page': 'active',
                       'isMemberOf': ismemberof,
                       'LDAPOther': ldapother,
                       'form': form,
                       'ns_messages': ns_messages})
    else:
        return render(request, 'profile.html', {'profile_page': 'active'})
