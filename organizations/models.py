from django.conf import settings
from django.db import models


class Organization(models.Model):
    KINDS = [('parishad', 'Zila Parishad'), ('city', 'City corporation')]

    code = models.SlugField(max_length=30, unique=True)
    name = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=160, blank=True)
    title = models.CharField(max_length=200)
    title_bn = models.CharField(max_length=240, blank=True)
    kind = models.CharField(max_length=20, choices=KINDS, default='parishad')
    head_title = models.CharField(
        max_length=60, default='Chairman',
        help_text='Shown for the head of the organisation. A corporation may be run by an '
                  'administrator instead of a mayor, so this label is editable.',
    )
    head_name = models.CharField(max_length=120, blank=True)
    address = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=40, blank=True)
    theme = models.CharField(max_length=20, default='parishad')
    is_active = models.BooleanField(default=True)
    sort = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['sort', 'name']

    def __str__(self):
        return self.name

    @property
    def emblem_text(self):
        return {'city': 'DSCC', 'parishad': 'GZP'}.get(self.kind, self.code.upper())

    @property
    def display_title(self):
        return self.title

    @property
    def is_city(self):
        return self.kind == 'city'


class Zone(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='zones')
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=160, blank=True)

    class Meta:
        ordering = ['organization', 'number']
        unique_together = [('organization', 'number')]

    def __str__(self):
        return f'{self.organization.code} zone {self.number}'


class Ward(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='wards')
    zone = models.ForeignKey(Zone, on_delete=models.CASCADE, related_name='wards')
    number = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=120)
    name_bn = models.CharField(max_length=160, blank=True)
    councillor_name = models.CharField(max_length=120, blank=True)
    councillor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name='wards', help_text='Demo login linked to this ward.',
    )

    class Meta:
        ordering = ['organization', 'number']
        unique_together = [('organization', 'number')]

    def __str__(self):
        return f'{self.organization.code} ward {self.number}'

    @property
    def label(self):
        return f'Ward {self.number}'
