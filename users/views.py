from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib import messages

from apache_kafka.models import Message
from apache_kafka.views import index_page_messages, check_for_new_messages
from comanage.models import IsMemberOf, LdapOther, NotaryServiceUser
from .cilogon import generate_cilogon_certificates, get_authorization_url, download
from .forms import UserPreferences, CILogonCertificateForm
from .models import Role


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


def authresponse(request):
    auth_response = request.GET.get('code', '-1')
    return render(
        request, 'authresponse.html',
        {
            "profile_page": "active",
            "auth_response": auth_response,
        }
    )

def set_role_boolean(user):
    user.is_nsadmin = (int(user.role) == int(getattr(Role, 'NSADMIN')))
    user.is_nsstaff = (int(user.role) == int(getattr(Role, 'STAFF')))
    user.is_pi = (int(user.role) == int(getattr(Role, 'PI_MEMBER')))
    user.is_piadmin = (int(user.role) == int(getattr(Role, 'PI_ADMIN')))
    user.is_dp = (int(user.role) == int(getattr(Role, 'DP')))
    user.is_inp = (int(user.role) == int(getattr(Role, 'INP')))
    user.is_ig = (int(user.role) == int(getattr(Role, 'IG')))
    user.is_norole = (int(user.role) == int(getattr(Role, 'NO_ROLE')))
    user.save()


def profile(request):
    if request.user.is_authenticated:
        user = get_object_or_404(NotaryServiceUser, id=request.user.id)
        # for user profile
        ismemberof = IsMemberOf.objects.filter(
            membershipismemberof__user_id=request.user.id).order_by('value')
        ldapother = LdapOther.objects.filter(
            membershipldapother__user_id=request.user.id).order_by('attribute', 'value')
        # for cilogon certificate
        auth_url = get_authorization_url()
        certificate_files = ''
        if request.method == "POST":
            # for user profile
            preference_form = UserPreferences(request.POST, instance=user, user=request.user)
            if preference_form.is_valid():
                if request.POST.get("delete-message"):
                    message = get_object_or_404(Message, uuid=request.POST.get('remove_message_uuid'))
                    message.is_active = False
                    message.save()
                if request.POST.get("update-preferences"):
                    user.show_uuid = preference_form.data.get('show_uuid')
                    user.role = preference_form.data.get('role')
                    user.save()
                    set_role_boolean(user=user)
                    messages.success(request, 'Preferences changed successfully!')
                if request.POST.get("check-messages"):
                    check_for_new_messages(str(request.user.uuid))
                return redirect('profile')
            # for cilogon certificate
            if request.POST.get("download"):
                if request.POST.get("path-cilogon.crt"):
                    path = request.POST.get("path-cilogon.crt")
                elif request.POST.get("path-cilogon.key"):
                    path = request.POST.get("path-cilogon.key")
                else:
                    path = request.POST.get("path-cilogon.p12")
                return download(request, path=path)
            certificate_form = CILogonCertificateForm(request.POST or None)
            if certificate_form.is_valid():
                if request.POST.get("generate-certificate"):
                    if str(request.POST.get('use_my_key')) == "True":
                        # TODO allow user to upload private key for CSR generation
                        pass
                    else:
                        certificate_files = generate_cilogon_certificates(
                            user=user,
                            authorization_response=str(request.POST.get("authorization_response")),
                            p12_password=str(request.POST.get("p12_password")),
                        )
                        user.cilogon_certificate_date = timezone.now()
                        user.save()
        else:
            preference_form = UserPreferences(instance=user, user=request.user)
            certificate_form = CILogonCertificateForm(request.POST)
        
        ns_messages = Message.objects.filter(
            kafka_topic=str(request.user.uuid),
            is_active=True
        ).order_by('-created_date')[:5]
        return render(request, 'profile.html',
                      {'profile_page': 'active',
                       'isMemberOf': ismemberof,
                       'LDAPOther': ldapother,
                       'preference_form': preference_form,
                       'role': get_object_or_404(Role, id=user.role).get_id_display(),
                       'ns_messages': ns_messages,
                       'certificate_form': certificate_form,
                       'auth_url': auth_url,
                       'certificate_files': certificate_files})
    else:
        return render(request, 'profile.html', {'profile_page': 'active'})
