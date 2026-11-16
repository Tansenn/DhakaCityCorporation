"""Create the Dhaka South City Corporation demo data.

Usage:
    python manage.py seed_organizations
"""
from __future__ import annotations

from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from accounts.demo import DEMO_PASSWORD
from accounts.models import Permission, Role, User
from accounts.permissions import PERMISSIONS, ROLE_DEFINITIONS, ROLE_PERMISSIONS
from core.models import AppSetting
from hr.models import Department
from organizations.data import (
    CITY_ACCOUNTS,
    CITY_DEPARTMENTS,
    CITY_FORMS,
    CITY_SERVICES,
    ORGANIZATIONS,
    VERIFICATION_STAGES,
    ZONES,
    councillor_name,
)
from organizations.models import Organization, Ward
from services.models import (
    ApplicationAction,
    Service,
    ServiceApplication,
    ServiceForm,
    VerificationRoute,
)
from services.pdfs import sample_value


class Command(BaseCommand):
    help = 'Create or refresh the organisation switcher and the DSCC demo data.'

    @transaction.atomic
    def handle(self, *args, **options):
        organizations = {}
        for row in ORGANIZATIONS:
            if row['code'] != 'dscc':
                continue
            org, _ = Organization.objects.update_or_create(
                code=row['code'], defaults={key: value for key, value in row.items()
                                            if key != 'code'})
            organizations[org.code] = org
        dscc = organizations['dscc']

        AppSetting.objects.update_or_create(
            key='app_name',
            defaults={'value': settings.APP_NAME, 'label': 'Application name',
                      'group': 'General'})
        AppSetting.objects.update_or_create(
            key='organisation_name',
            defaults={'value': settings.ORGANISATION, 'label': 'Organisation name',
                      'group': 'General'})

        self._roles(dscc)
        users = self._users(dscc)
        self._departments(dscc)
        self._zones_and_wards(dscc, users)
        services = self._services(dscc)
        forms = self._forms(dscc, services)
        self._routes(dscc)
        self._sample_applications(dscc, forms, users)

        self.stdout.write(self.style.SUCCESS(
            'Organisations ready: %s. DSCC: %d services, %d forms, %d zones, %d wards.'
            % (', '.join(o.name for o in organizations.values()), len(services),
               len(forms), dscc.zones.count(), dscc.wards.count())))

    def _roles(self, dscc):
        perms = {}
        for code, label, module in PERMISSIONS:
            perm, _ = Permission.objects.update_or_create(
                code=code, defaults={'label': label, 'module': module})
            perms[code] = perm
        labels = {code: label for _username, _full_name, code, label, _org in CITY_ACCOUNTS}
        for code in ('dscc_councillor', 'dscc_officer', 'dscc_mayor'):
            role, _ = Role.objects.update_or_create(
                code=code, defaults={'name': labels[code], 'organization': dscc})
            role.permissions.set(
                [perms[item] for item in ROLE_PERMISSIONS.get(code, []) if item in perms])
        definitions = {row[0]: row for row in ROLE_DEFINITIONS}
        for code in ('admin', 'citizen'):
            _code, name, description, sort_order, is_read_only = definitions[code]
            role, _ = Role.objects.get_or_create(
                code=code, defaults={
                    'name': name, 'description': description,
                    'sort_order': sort_order, 'is_read_only': is_read_only})
            role.permissions.add(*[perms[item] for item in ROLE_PERMISSIONS.get(code, [])
                                   if item in perms])

    def _users(self, dscc):
        users = {}
        for username, full_name, role_code, label, _org in CITY_ACCOUNTS:
            parts = full_name.split()
            role = Role.objects.filter(code=role_code).first()
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@example.test',
                    'first_name': parts[0],
                    'last_name': ' '.join(parts[1:]),
                    'phone': '01711000021',
                    'role': role,
                    'organization': dscc,
                    'email_verified': True,
                    'is_demo': True,
                })
            if created:
                user.set_password(DEMO_PASSWORD)
            user.role = role
            user.organization = dscc
            user.email_verified = True
            user.save()
            users[username] = user
        return users

    def _departments(self, dscc):
        # (organization, name) is unique, so park every name before renaming;
        # otherwise one row's new name can collide with a name another row holds.
        for index, department in enumerate(
                Department.objects.filter(organization=dscc).order_by('code')):
            Department.objects.filter(pk=department.pk).update(
                name=f'__dscc_pending_{index}')
        for index, department in enumerate(CITY_DEPARTMENTS, start=1):
            Department.objects.update_or_create(
                code=f'dscc-dept-{index:02d}',
                defaults={'name': department['name'], 'organization': dscc})
        return Department.objects.filter(organization=dscc)

    def _zones_and_wards(self, dscc, users):
        councillor = users.get('dscc_councillor')
        number = 1
        for zone_number, zone_name, zone_name_bn, ward_count in ZONES:
            zone, _ = dscc.zones.update_or_create(
                number=zone_number,
                defaults={'name': zone_name, 'name_bn': zone_name_bn})
            for _ in range(ward_count):
                ward, _ = dscc.wards.update_or_create(
                    number=number,
                    defaults={
                        'zone': zone,
                        'name': f'Ward {number}',
                        'name_bn': f'ওয়ার্ড {number}',
                        'councillor_name': councillor_name(number),
                    })
                number += 1
        first_ward = dscc.wards.filter(number=1).first()
        if first_ward and councillor:
            first_ward.councillor = councillor
            first_ward.councillor_name = councillor.display_name
            first_ward.save(update_fields=['councillor', 'councillor_name'])
        for ward in dscc.wards.filter(councillor__isnull=True):
            if not ward.councillor_name:
                ward.councillor_name = councillor_name(ward.number)
                ward.save(update_fields=['councillor_name'])

    def _services(self, dscc):
        services = {}
        for sort, row in enumerate(CITY_SERVICES, start=1):
            service, _ = Service.objects.update_or_create(
                organization=dscc, code=row['code'],
                defaults={
                    'name': row['name'],
                    'name_bn': row['name_bn'],
                    'icon': row['icon'],
                    'department': row['department'],
                    'summary': row['summary'],
                    'fee': row['fee'],
                    'processing_days': row['processing_days'],
                    'requirements': row.get('requirements', ''),
                    'sort': sort,
                    'is_active': True,
                })
            services[service.code] = service
        return services

    def _forms(self, dscc, services):
        forms = {}
        for sort, row in enumerate(CITY_FORMS, start=1):
            sl, title, title_bn, code, form_type, category, has_sample, fields = row
            form, _ = ServiceForm.objects.update_or_create(
                organization=dscc, sl=sl,
                defaults={
                    'service': services.get(code),
                    'title': title,
                    'title_bn': title_bn,
                    'form_no': f'DSCC/FRM/2026/{sl:03d}',
                    'form_type': form_type,
                    'category': category,
                    'fields': '\n'.join(fields),
                    'has_sample': has_sample,
                    'sort': sort,
                })
            forms[sl] = form
        return forms

    def _routes(self, dscc):
        for order, role_code, label, is_final in VERIFICATION_STAGES:
            role = Role.objects.filter(code=role_code).first()
            if not role:
                continue
            VerificationRoute.objects.update_or_create(
                organization=dscc, service=None, order=order,
                defaults={'role': role, 'label': label, 'is_final': is_final})

    def _sample_applications(self, dscc, forms, users):
        citizen = users.get('dscc_citizen')
        councillor = users.get('dscc_councillor')
        officer = users.get('dscc_officer')
        mayor = users.get('dscc_mayor')
        ward = Ward.objects.filter(organization=dscc, number=1).first()
        if not all([citizen, councillor, officer, mayor, ward]):
            return
        year = timezone.localdate().year
        seeds = [
            (1, 'submitted', 1, [], 2),
            (3, 'in_review', 2, ['councillor'], 2),
            (7, 'approved', 3, ['councillor', 'officer', 'mayor'], 12),
            (9, 'returned', 1, ['return'], 5),
        ]
        actors = {'councillor': councillor, 'officer': officer, 'mayor': mayor}
        order_labels = {1: 'Ward councillor verification', 2: 'Department verification',
                        3: 'Final approval'}
        decisions = {'councillor': 'verify', 'officer': 'verify', 'mayor': 'approve',
                     'return': 'return'}
        for index, (sl, status, current_order, steps, age) in enumerate(seeds, start=1):
            form = forms.get(sl)
            if form is None:
                continue
            labels = [spec['label'] for spec in form.field_specs()
                      if spec['kind'] == 'field'][:7]
            data = {label: sample_value(label) for label in labels}
            reference = f'DSCC-{year}-{index:04d}'
            created = timezone.now() - timedelta(days=age)
            application, _ = ServiceApplication.objects.update_or_create(
                reference=reference,
                defaults={
                    'organization': dscc, 'form': form, 'service': form.service,
                    'applicant': citizen, 'ward': ward, 'data': data,
                    'status': status, 'current_order': current_order,
                    'created_at': created,
                    'decided_at': timezone.now() if status in ('approved', 'rejected') else None,
                })
            application.actions.all().delete()
            ApplicationAction.objects.create(
                application=application, order=0, label='Application submitted',
                role_code='citizen', actor=citizen, decision='verify',
                comments='Submitted through the online form', created_at=created)
            span = timezone.now() - created
            for step_index, actor_key in enumerate(steps, start=1):
                actor = actors.get(actor_key) or councillor
                ApplicationAction.objects.create(
                    application=application,
                    order=1 if actor_key == 'return' else step_index,
                    label=(order_labels[1] if actor_key == 'return'
                           else order_labels[step_index]),
                    role_code=actor.role.code if actor.role else '',
                    actor=actor, decision=decisions[actor_key],
                    comments=('Please attach the updated document.' if actor_key == 'return'
                              else 'Verified against the submitted documents.'),
                    created_at=created + span * step_index / (len(steps) + 1))
