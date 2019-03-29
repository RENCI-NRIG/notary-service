import os

from django import template
from users.models import Role

register = template.Library()


@register.filter
def rolename(value):
    return str(Role.objects.get(id=value))


@register.simple_tag(takes_context=True)
def display_search(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_staff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_projects(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_staff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_datasets(context):
    u = context['request'].user
    if u.is_nsadmin or u.is_staff or u.is_pi or u.is_piadmin or u.is_dp or u.is_inp or u.is_ig:
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
