from django.shortcuts import render, get_object_or_404, HttpResponseRedirect, redirect

from .consumer import check_for_new_messages
from .models import Message


def messages(request):
    if request.user.is_authenticated:
        show_active = True
        ns_messages = Message.objects.filter(
            kafka_topic=str(request.user.uuid)
        )
        if request.method == "POST":
            if request.POST.get("check-messages"):
                check_for_new_messages(str(request.user.uuid))
            elif request.POST.get("delete-message"):
                message = get_object_or_404(Message, uuid=request.POST.get('remove_message_uuid'))
                if message.is_active:
                    # if message is active, move it to the trash
                    message.is_active = False
                    message.save()
                else:
                    # if message is in trash, delete it
                    message.delete()
            if request.POST.get("show-active"):
                show_active = True
            elif request.POST.get("show-trash"):
                show_active = False
        ns_messages = ns_messages.filter(is_active=show_active).order_by('-created_date')
        return render(request, 'messages.html',
                      {"profile_page": "active", 'ns_messages': ns_messages, 'show_active': show_active})
    else:
        return redirect('index')


def index_page_messages(request):
    if request.user.is_authenticated:
        if request.method == "POST":
            if request.POST.get("check-messages"):
                check_for_new_messages(str(request.user.uuid))
        ns_messages = Message.objects.filter(
            kafka_topic=str(request.user.uuid),
            is_active=True).order_by('-created_date')[:5]
        return render(request, 'index.html', {"index_page": "active", 'ns_messages': ns_messages})
    else:
        return redirect('index')


def message_detail(request, uuid):
    if request.user.is_authenticated:
        message = get_object_or_404(Message, uuid=uuid)
        if request.method == "POST":
            if request.POST.get("return-to-list"):
                return redirect('messages')
            elif request.POST.get("delete-message"):
                message = get_object_or_404(Message, uuid=request.POST.get('remove_message_uuid'))
                if message.is_active:
                    # if message is active, move it to the trash
                    message.is_active = False
                    message.save()
                else:
                    # if message is in trash, delete it
                    message.delete()
            elif request.POST.get("undelete-message"):
                message.is_active = True
                message.save()
            return redirect('messages')
        return render(request, 'message_detail.html', {
            'profile_page': 'active',
            'message': message
        })
    else:
        return redirect('index')
