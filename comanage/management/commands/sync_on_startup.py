# comanage/management/commands/sync_on_startup.py
import json
import datetime
import os

from django.core.management.base import BaseCommand, CommandError
from comanage import api, logger
from users.models import NotaryServiceUser, ComanageCou, ns_roles
from projects.models import Project
from comanage.comanage_api import add_co_cou, verify_ns_cou, add_co_user, verify_ns_user, add_co_affiliation, \
    verify_ns_affiliation, add_co_person_roles, verify_ns_person_roles, add_co_project, verify_ns_project


def add_comanage_cous():
    co_cous = api.cous_view_per_co().get('Cous', [])
    for co_cou in co_cous:
        add_co_cou(co_cou=co_cou)


def verify_notary_cous():
    ns_cous = ComanageCou.objects.all().order_by('id')
    for ns_cou in ns_cous:
        verify_ns_cou(ns_cou=ns_cou)


def add_comanage_users():
    co_people = api.copeople_view_per_co().get('CoPeople', [])
    for co_person in co_people:
        add_co_user(co_person=co_person)
        add_co_affiliation(co_person=co_person)
        add_co_person_roles(co_person=co_person)


def verify_notary_users():
    ns_people = NotaryServiceUser.objects.all().order_by('id')
    for ns_person in ns_people:
        verify_ns_user(ns_person=ns_person)
        verify_ns_affiliation(ns_person=ns_person)
        verify_ns_person_roles(ns_person=ns_person)


def add_comanage_projects():
    co_cous = api.cous_view_per_co().get('Cous', [])
    if co_cous:
        ns_project_uuids = []
        ns_roles.append('Projects')
        for co_cou in co_cous:
            if co_cou.get('Name') not in ns_roles:
                project_uuid = str(co_cou.get('Name')).rsplit('-', 1)[0]
                if project_uuid not in ns_project_uuids:
                    ns_project_uuids.append(project_uuid)
        for ns_project_uuid in ns_project_uuids:
            add_co_project(project_uuid=ns_project_uuid)


def verify_notary_projects():
    ns_projects = Project.objects.all().order_by('id')
    if ns_projects:
        for ns_project in ns_projects:
            verify_ns_project(ns_project=ns_project)


class Command(BaseCommand):
    help = 'COmanage sync on startup'

    def handle(self, *args, **kwargs):
        try:
            logger.info(
                '{0} - ### Sync COmanage data with Notary Service data ###'.format(datetime.datetime.now().ctime()))
            logger.info(
                '{0} - ### Add COmanage Cous ###'.format(datetime.datetime.now().ctime()))
            add_comanage_cous()
            logger.info(
                '{0} - ### Verify Notary Cous ###'.format(datetime.datetime.now().ctime()))
            verify_notary_cous()
            logger.info(
                '{0} - ### Add COmanage Users ###'.format(datetime.datetime.now().ctime()))
            add_comanage_users()
            logger.info(
                '{0} - ### Verify Notary Users ###'.format(datetime.datetime.now().ctime()))
            verify_notary_users()
            logger.info(
                '{0} - ### Add COmanage Projects ###'.format(datetime.datetime.now().ctime()))
            add_comanage_projects()
            logger.info(
                '{0} - ### Verify Notary Projects ###'.format(datetime.datetime.now().ctime()))
            verify_notary_projects()

        except Exception as e:
            print(e)
            raise CommandError('Initalization failed.')
