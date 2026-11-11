from decimal import Decimal

from django.db import models
from django.utils import timezone


class Facility(models.Model):
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    location = models.CharField(max_length=200)
    amenities = models.TextField(blank=True, help_text='Comma-separated list.')
    rules = models.TextField(blank=True)
    booking_types = models.CharField(
        max_length=200, blank=True,
        help_text='Permitted booking types, e.g. individual stay, official meeting.',
    )
    photo = models.ImageField(upload_to='facilities/', blank=True)
    contact = models.CharField(max_length=120, blank=True)
    is_sample = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'Facilities'

    def __str__(self):
        return self.name

    @property
    def amenity_list(self):
        return [a.strip() for a in (self.amenities or '').split(',') if a.strip()]

    @property
    def tariff_categories(self):
        return Tariff.CATEGORIES

    @property
    def lowest_tariff(self):
        tariff = (Tariff.objects.filter(
                      unit__facility=self, unit__is_active=True,
                      unit__asset_category='dakbungalow')
                  .order_by('amount').first())
        return tariff.amount if tariff else None


class Unit(models.Model):
    KINDS = [
        ('room', 'Room'),
        ('suite', 'VIP suite'),
        ('hall', 'Conference hall'),
        ('asset', 'Daily reservation'),
    ]
    ASSET_CATEGORIES = [
        ('land', 'Lands'), ('ponds', 'Ponds'), ('markets', 'Markets'),
        ('kheyaghat', 'Kheyaghat'), ('auditorium', 'Auditorium'),
        ('dakbungalow', 'Dakbungalows'),
    ]
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE, related_name='units')
    code = models.SlugField(max_length=40)
    name = models.CharField(max_length=120)
    kind = models.CharField(max_length=10, choices=KINDS, default='room')
    asset_category = models.CharField(max_length=20, choices=ASSET_CATEGORIES, default='dakbungalow')
    capacity = models.PositiveIntegerField(default=2)
    description = models.CharField(max_length=255, blank=True)
    amenities = models.CharField(max_length=255, blank=True)
    photo = models.ImageField(upload_to='units/', blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['facility', 'kind', 'name']
        unique_together = [('facility', 'code')]

    def __str__(self):
        return f'{self.facility.name} - {self.name}'

    @property
    def catalogue_image(self):
        return f'img/asset-{self.asset_category}.jpg'

    @property
    def is_hall(self):
        return self.kind == 'hall'

    @property
    def is_suite(self):
        return self.kind == 'suite'


class Tariff(models.Model):
    CATEGORIES = [
        ('government', 'Government official'),
        ('citizen', 'Public citizen'),
        ('organization', 'Organization'),
    ]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='tariffs')
    category = models.CharField(max_length=20, choices=CATEGORIES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    holiday_amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text='Nightly / slot rate on Fridays, Saturdays and declared holidays.',
    )
    deposit = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    is_sample = models.BooleanField(default=True)

    class Meta:
        ordering = ['unit', 'category']
        unique_together = [('unit', 'category')]

    def __str__(self):
        return f'{self.unit} / {self.category}'


class BlackoutDate(models.Model):
    facility = models.ForeignKey(Facility, on_delete=models.CASCADE,
                                 related_name='blackout_dates')
    date = models.DateField()
    reason = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['date']
        unique_together = [('facility', 'date')]

    def __str__(self):
        return f'{self.facility.name} {self.date}'


class InventoryLock(models.Model):
    """A nightly lock (rooms/suites) or a slot lock (conference halls).

    One row per unit per date (rooms) or per unit per date per slot (halls).
    A partial unique constraint prevents two active locks on the same inventory.
    Temporary holds have hold_expires_at set; confirmed bookings have it null.
    """
    SLOTS = [
        ('', 'Full day / room'),
        ('morning', 'Morning'),
        ('afternoon', 'Afternoon'),
        ('evening', 'Evening'),
    ]
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='locks')
    date = models.DateField()
    slot = models.CharField(max_length=12, choices=SLOTS, blank=True, default='')
    booking = models.ForeignKey('bookings.Booking', null=True, blank=True,
                                on_delete=models.SET_NULL, related_name='locks')
    hold_expires_at = models.DateTimeField(null=True, blank=True)
    released = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['date']
        constraints = [
            models.UniqueConstraint(
                fields=['unit', 'date', 'slot'],
                condition=models.Q(released=False),
                name='uniq_active_inventory_lock',
            ),
        ]

    def __str__(self):
        return f'{self.unit} {self.date} {self.slot or "room"}'

    @property
    def is_active(self):
        if self.released:
            return False
        if self.hold_expires_at and self.hold_expires_at <= timezone.now():
            return False
        return True
