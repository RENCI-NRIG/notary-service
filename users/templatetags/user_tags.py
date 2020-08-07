from django import template
from django.core.exceptions import ObjectDoesNotExist

from users.models import Role, Affiliation, NotaryServiceUser
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def get_obj_attr(obj, attr):
    return getattr(obj, attr)

@register.filter
def rolename(value):
    return str(Role.objects.get(id=value))

@register.filter
def cert_exp_datetime(start_time):
    return start_time + timedelta(days=10)


@register.filter
def affiliation_from_comanage_uid(user_uid):
    try:
        user_aff = NotaryServiceUser.objects.get(
            sub=user_uid
        ).idp_name
    except NotaryServiceUser.DoesNotExist:
        user_aff = 'User has not interacted with system yet'
    return user_aff


@register.filter
def affiliation_uuid_to_name(uuid):
    return str(Affiliation.objects.get(uuid=uuid).display_name)


@register.simple_tag(takes_context=True)
def display_search(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_nsstaff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_projects(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_nsstaff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_datasets(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_nsstaff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_templates(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_piadmin or u.is_dp:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_workflows(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_nsstaff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_infrastructure(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_nsstaff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False
