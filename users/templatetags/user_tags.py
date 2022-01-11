from django import template
from django.core.exceptions import ObjectDoesNotExist

from users.models import Role, Affiliation, NotaryServiceUser, CilogonCertificate
from datetime import datetime, timedelta
from cryptography.x509 import load_pem_x509_certificate

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
    if u.is_nsadmin() or u.is_active and u.is_impact_user():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_projects(context):
    u = context['request'].user
    if u.is_nsadmin() or u.is_active and u.is_impact_user():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_datasets(context):
    u = context['request'].user
    if u.is_nsadmin() or u.is_active and u.is_impact_user():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_templates(context):
    u = context['request'].user
    if u.is_nsadmin() or u.is_active and u.is_dp() and u.is_impact_user():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_workflows(context):
    u = context['request'].user
    if u.is_nsadmin() or u.is_active and u.is_impact_user():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_infrastructure(context):
    u = context['request'].user
    if u.is_nsadmin() or u.is_inp() or u.is_pi():
        return True
    else:
        return False


@register.simple_tag(takes_context=True)
def display_nsadmin(context):
    u = context['request'].user
    if u.is_nsadmin():
        return True
    else:
        return False


@register.filter
def cert_not_before_from_pubkey(uuid):
    c = CilogonCertificate.objects.filter(uuid=uuid).first()
    cert = load_pem_x509_certificate(str.encode(c.pubkey))

    return cert.not_valid_before


@register.filter
def cert_not_after_from_pubkey(uuid):
    c = CilogonCertificate.objects.filter(uuid=uuid).first()
    cert = load_pem_x509_certificate(str.encode(c.pubkey))

    return cert.not_valid_after

