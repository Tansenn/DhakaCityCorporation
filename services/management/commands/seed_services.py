"""Populate the public service directory and the application form library."""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from organizations.models import Organization
from services.data import FORMS, SERVICES
from services.models import Service, ServiceForm


class Command(BaseCommand):
    help = 'Create or refresh the demo service directory and form library.'

    def handle(self, *args, **options):
        org = Organization.objects.filter(code='gzp').first()
        with transaction.atomic():
            services = {}
            for sort, row in enumerate(SERVICES, start=1):
                service, _ = Service.objects.update_or_create(
                    organization=org, code=row['code'],
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

            for sort, row in enumerate(FORMS, start=1):
                sl, title, title_bn, code, form_type, category, has_sample, fields = row
                ServiceForm.objects.update_or_create(
                    organization=org, sl=sl,
                    defaults={
                        'service': services.get(code) if code else None,
                        'title': title,
                        'title_bn': title_bn,
                        'form_no': f'GZP/SVC/2026/{sl:03d}',
                        'form_type': form_type,
                        'category': category,
                        'fields': '\n'.join(fields),
                        'has_sample': has_sample,
                        'sort': sort,
                    })

        self.stdout.write(self.style.SUCCESS(
            'Service directory ready: %d services, %d forms.'
            % (Service.objects.filter(organization=org).count(),
               ServiceForm.objects.filter(organization=org).count())))
