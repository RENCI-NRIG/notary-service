import mimetypes
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, Http404
from django.shortcuts import render, get_object_or_404

from nsmessages.nsmessages import NsMessages
from .cilogon import x509_generate_cilogon_certificate, \
    user_cilogon_certificates_directory_path
from .models import NotaryServiceUser, ns_roles


def index(request):
    if request.user.is_authenticated:
        nsmessages = NsMessages.objects.filter(
            users_to__in=[request.user]
        ).order_by('-created')[:3]
        new_message_count = len(NsMessages.objects.filter(
            users_to__in=[request.user],
            is_read=False
        ).distinct())
        return render(request, 'index.html', {'index_page': 'active', 'nsmessages': nsmessages,
                                              'new_messages': new_message_count})
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


@login_required()
def profile(request):
    if request.POST.get("generate-cilogon-certificate"):
        oidc_access_token = request.session.get('oidc_access_token')
        p12_password = request.POST.get("p12-password")
        try:
            new_cert = x509_generate_cilogon_certificate(cilogon_access_token=oidc_access_token,
                                                         p12_password=p12_password)
            if new_cert:
                if request.user.cilogon_cert:
                    old_cert = request.user.cilogon_cert
                    request.user.cilogon_cert = new_cert
                    request.user.save()
                    old_cert.delete()
                else:
                    request.user.cilogon_cert = new_cert
                    request.user.save()
                messages.success(request, '[INFO] A new CILogon Certificate has been generated')
            else:
                messages.error(request, '[ERROR] Unable to generate a new CILogon Certificate ...')
        except Exception as e:
            messages.error(request, '[ERROR] Unable to generate a new CILogon Certificate ... {0}'.format(e))

    if request.POST.get("download-pubkey"):
        return download_file(request,
                             filename='cilogon.cer',
                             cert_content=str.encode(request.user.cilogon_cert.pubkey))

    if request.POST.get("download-privkey"):
        return download_file(request,
                             filename='cilogon.key',
                             cert_content=str.encode(request.user.cilogon_cert.privkey))

    if request.POST.get("download-p12"):
        return download_file(request,
                             filename='cilogon.p12',
                             cert_content=request.user.cilogon_cert.p12)

    if request.user.is_authenticated:
        user = NotaryServiceUser.objects.filter(id=request.user.id).first()
        roles = user.roles.all().order_by("co_cou__name")
        sent_messages = NsMessages.objects.filter(users_from__in=[user]).order_by('-created')[:10]
        received_messages = NsMessages.objects.filter(users_to__in=[user]).order_by('is_read', '-created')[:10]
        new_message_count = len(NsMessages.objects.filter(
            users_to__in=[user],
            is_read=False
        ).distinct())
        return render(request, 'profile.html',
                      {'profile_page': 'active', 'user': user, 'roles': roles, 'ns_roles': ns_roles,
                       'sent_messages': sent_messages, 'received_messages': received_messages,
                       'new_messages': new_message_count})
    else:
        return render(request, 'profile.html', {'profile_page': 'active'})


@login_required()
def message_detail(request, uuid):
    message = get_object_or_404(NsMessages, uuid=uuid)
    users_to = message.users_to.all()
    users_from = message.users_from.all()
    if request.user in users_to:
        message.is_read = True
        message.save()

    return render(request, 'message_detail.html',
                  {'profile_page': 'active', 'user': request.user, 'message': message,
                   'users_to': users_to, 'users_from': users_from})


def download_file(request, filename: str, cert_content: bytes):
    dirpath = os.path.dirname(user_cilogon_certificates_directory_path(request.user))
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    filepath = dirpath + '/' + filename
    with open(filepath, 'wb') as fh:
        fh.write(cert_content)
    mime_type, _ = mimetypes.guess_type(filepath)
    if os.path.exists(filepath):
        with open(filepath, 'rb') as fh:
            response = HttpResponse(fh.read(), content_type=mime_type)
            response['Content-Disposition'] = "attachment; filename=%s" % filename
            # response['Content-Disposition'] = 'inline; filename=' + os.path.basename(filepath)
            return response
    raise Http404
