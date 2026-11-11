from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from facilities.models import Facility, Tariff, Unit


SAMPLES = {
    'land': [('Community green', 'Open lawn · 0.8 acre', 1800), ('Riverside field', 'Open plot · 1.2 acres', 2400), ('Garden grounds', 'Garden plot · 0.6 acre', 1600)],
    'ponds': [('Shapla pond', 'Waterside grounds · 0.5 acre', 1200), ('Greenbank pond', 'Shaded bank · 0.8 acre', 1600), ('Lotus pond', 'Community pond · 0.4 acre', 1000)],
    'markets': [('Morning bazaar stall', 'Covered stall · 120 sq ft', 500), ('Central market space', 'Trading space · 180 sq ft', 800), ('Village market stall', 'Corner stall · 100 sq ft', 400)],
    'kheyaghat': [('Turag landing', 'Riverside landing space', 2000), ('Shitalakshya landing', 'Sheltered river landing', 2200), ('Balu river ghat', 'Small community landing', 1500)],
    'auditorium': [('Parishad auditorium', 'Main hall · 400 seats', 12000), ('Community auditorium', 'Community hall · 200 seats', 7500), ('Garden auditorium', 'Meeting hall · 100 seats', 5000)],
}


class Command(BaseCommand):
    help = 'Add sample asset inventory without replacing existing records.'

    @transaction.atomic
    def handle(self, *args, **options):
        facilities = list(Facility.objects.filter(is_active=True).order_by('pk')[:4])
        if not facilities:
            raise CommandError('Run seed_demo first to create the four managed facilities.')
        created = 0
        for category, entries in SAMPLES.items():
            for index, (name, description, amount) in enumerate(entries):
                item, new = Unit.objects.get_or_create(
                    facility=facilities[index % len(facilities)], code=f'sample-{category}-{index + 1}',
                    defaults={'name': name, 'description': description, 'asset_category': category,
                              'kind': 'hall' if category == 'auditorium' else 'asset',
                              'capacity': [400, 200, 100][index] if category == 'auditorium' else 12,
                              'amenities': 'Managed access,Local assistance'},
                )
                created += new
                for applicant in ('citizen', 'government', 'organization'):
                    Tariff.objects.get_or_create(unit=item, category=applicant, defaults={
                        'amount': Decimal(amount), 'holiday_amount': Decimal(amount),
                        'deposit': Decimal('500'), 'is_sample': True,
                    })
        self.stdout.write(self.style.SUCCESS(f'Added {created} sample assets; existing data preserved.'))
