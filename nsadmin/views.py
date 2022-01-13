import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404

from comanage.comanage_api import create_co_person_role, remove_co_person_role
from nsmessages.nsmessages import send_nsmessage, NsMessages
from users.models import NotaryServiceUser, ComanageCou


@login_required()
def nsadmin(request):
    if request.user.is_nsadmin():
        if request.method == 'POST':
            for key in request.POST.keys():
                if not key == 'csrfmiddlewaretoken':
                    cur_value = request.POST.get(key)
                    parse_key = key.rsplit('_', 1)
                    ns_role = parse_key[0]
                    ns_user = NotaryServiceUser.objects.filter(id=int(parse_key[1])).first()
                    ns_cou = ComanageCou.objects.filter(name=ns_role).first()
                    if str(cur_value) == 'True':
                        blocked_cou_ids = [
                            str(os.getenv('COU_ID_ACTIVE_USER')),
                            str(os.getenv('COU_ID_NOTARY_SERVICE_ADMINS'))
                        ]
                        if ns_user == request.user and str(ns_cou.co_cou_id) in blocked_cou_ids:
                            messages.error(
                                request,
                                '[INFO] Cannot reemove role "{0}" from "self"'.format(ns_role))
                        else:
                            remove_co_person_role(co_person_id=ns_user.co_person_id, co_cou_id=ns_cou.co_cou_id)
                            messages.info(
                                request,
                                '[INFO] Remove role "{0}" from user "{1}"'.format(ns_role, ns_user.display_name))
                            if str(ns_cou.co_cou_id) == str(os.getenv('COU_ID_NOTARY_SERVICE_ADMINS')):
                                remove_co_person_role(
                                    co_person_id=ns_user.co_person_id,
                                    co_cou_id=int(os.getenv('COU_ID_ENROLLMENT_APPROVAL'))
                                )
                                messages.info(
                                    request,
                                    '[INFO] Remove role "{0}" to user "{1}"'.format(
                                        os.getenv('ROLE_ENROLLMENT_APPROVAL'),
                                        ns_user.display_name))
                            send_nsmessage(
                                users_to=[ns_user],
                                users_from=[request.user],
                                subject='[ROLE] "{0}" has been removed'.format(ns_role),
                                body="""
Role "{0}" has been removed

See /profile for your current Notary Service roles                           
""".format(ns_role)
                            )
                    else:
                        create_co_person_role(co_person_id=ns_user.co_person_id, co_cou_id=ns_cou.co_cou_id)
                        messages.info(
                            request,
                            '[INFO] Add role "{0}" to user "{1}"'.format(ns_role, ns_user.display_name))
                        # add EnrollmentApproval if request is for NotaryServiceAdmin
                        if str(ns_cou.co_cou_id) == str(os.getenv('COU_ID_NOTARY_SERVICE_ADMINS')):
                            create_co_person_role(
                                co_person_id=ns_user.co_person_id,
                                co_cou_id=int(os.getenv('COU_ID_ENROLLMENT_APPROVAL'))
                            )
                            messages.info(
                                request,
                                '[INFO] Add role "{0}" to user "{1}"'.format(os.getenv('ROLE_ENROLLMENT_APPROVAL'),
                                                                             ns_user.display_name))
                        send_nsmessage(
                            users_to=[ns_user],
                            users_from=[request.user],
                            subject='[ROLE] "{0}" has been added'.format(ns_role),
                            body="""
Role "{0}" has been added

See /profile for your current Notary Service roles                           
""".format(ns_role)
                        )

        ns_people = NotaryServiceUser.objects.all().order_by('display_name')
        nsmessages = NsMessages.objects.all().order_by('-created')[:25]
        ns_messages = []
        for m in nsmessages:
            users_to = m.users_to.all().values_list('display_name', flat=True)
            users_from = m.users_from.all().values_list('display_name', flat=True)
            ns_messages.append({
                'uuid': m.uuid,
                'subject': m.subject,
                'created': m.created,
                'is_read': m.is_read,
                'users_to': users_to,
                'users_from': users_from
            })
        return render(request, 'nsadmin.html',
                      {
                          'people': ns_people,
                          'nsmessages': ns_messages,
                          'nsadmin_page': 'active'
                      })
    else:
        return render(request, 'index.html')


@login_required()
def nsadminmessage_detail(request, uuid):
    message = get_object_or_404(NsMessages, uuid=uuid)
    users_to = message.users_to.all()
    users_from = message.users_from.all()

    return render(request, 'nsadminmessage_detail.html',
                  {'profile_page': 'active', 'user': request.user, 'message': message,
                   'users_to': users_to, 'users_from': users_from})
