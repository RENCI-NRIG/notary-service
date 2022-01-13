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
Hello, {0},

Welcome to the ImPACT Notary Service!

-NSAdmin
""".format(user.display_name)
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
        subject='[REQUEST TO JOIN] Project "{0}"'.format(project.name),
        body="""
Hello,

User "{0}" is requesting to join your Project "{1}"
You can add them from: {2}.

Any questions regarding this request should be directed to: {3}

""".format(request.user.display_name, project.name, members_link, request.user.email)
    )

    return True


def role_added_to_project(request, user: NotaryServiceUser, project: Project, role: str) -> bool:
    project_link = request.scheme + '://' + request.get_host() + '/projects/' + str(project.uuid)
    send_nsmessage(
        users_to=[user],
        users_from=[request.user],
        subject='[PROJECT] Role added to project "{0}"'.format(project.name),
        body="""
Hello, {0},

The Role of "{1}" has been added for you to Project "{2}" by User "{3}".
Project details can be found at: {4}

Any questions regarding this change should be directed to: {5}

""".format(user.display_name, role, project.name, request.user.display_name, project_link, request.user.email)
    )

    return True


def role_removed_from_project(request, user: NotaryServiceUser, project: Project, role: str) -> bool:
    send_nsmessage(
        users_to=[user],
        users_from=[request.user],
        subject='[PROJECT] Role removed from project "{0}"'.format(project.name),
        body="""
Hello, {0},

The Role of "{1}" has been removed for you from Project "{2}" by User "{3}".

Any questions regarding this change should be directed to: {4}

""".format(user.display_name, role, project.name, request.user.display_name, request.user.email)
    )

    return True
