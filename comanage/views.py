from django.shortcuts import render

from comanage.models import IsMemberOf, LdapOther


def group_list(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
    else:
        user_id = 0
    membership = IsMemberOf.objects.filter(membershipismemberof__user_id=user_id).order_by('value')
    return render(request, 'profile.html', {'isMemberOf': membership})


def ldap_other_list(request):
    if request.method == 'POST':
        user_id = request.POST['user_id']
    else:
        user_id = 0
    membership = LdapOther.objects.filter(membershipldapother__user_id=user_id).order_by('attribute', 'value')
    return render(request, 'profile.html', {'LDAPOther': membership})
