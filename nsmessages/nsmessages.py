from uuid import uuid4

from users.models import NotaryServiceUser
from .models import NsMessages
from projects.models import Project
from django.db.models import Q


def send_nsmessage(users_to: [NotaryServiceUser], users_from: [NotaryServiceUser], subject: str, body: str) -> bool:
    nsmessage = NsMessages()
    nsmessage.uuid = uuid4()
    nsmessage.subject = subject
    nsmessage.body = body
    nsmessage.is_read = False
    nsmessage.save()
    for ns_user in users_to:
        nsmessage.users_to.add(ns_user)
    for ns_user in users_from:
        nsmessage.users_from.add(ns_user)
    nsmessage.save()

    return True


def send_welcome_message(user: NotaryServiceUser) -> bool:
    send_nsmessage(
        users_to=[user],
        users_from=[],
        subject='[WELCOME] New member of the ImPACT Notary Service',
        body="""
Welcome to the ImPACT Notary Service

-NSAdmin
"""
    )

    return True


def join_project_request(request, project: Project) -> bool:
    proj_users = NotaryServiceUser.objects.filter(
        Q(uuid__in=project.comanage_pi_admins.all().values('uuid')) |
        Q(uuid__in=project.comanage_pi_members.all().values('uuid'))
    ).order_by('display_name').distinct('display_name')
    users_to = [u for u in proj_users]
    members_link = request.scheme + '://' + request.get_host() + '/projects/' + str(project.uuid) + '#project-members'
    send_nsmessage(
        users_to=users_to,
        users_from=[request.user],
        subject='[JOIN] Request to join Project "{0}"'.format(project.name),
        body="""
User "{0}" is requesting to join Project "{1}"
You can add them from: {2}.

For further questions regarding this request send email to: {3}

""".format(request.user.display_name, project.name, members_link, request.user.email)
    )

    return True
