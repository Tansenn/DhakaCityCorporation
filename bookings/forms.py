from datetime import timedelta

from django import forms
from django.utils import timezone

from core.models import get_int
from facilities.availability import SLOT_CHOICES, is_free, tariff_for
from facilities.models import Facility, Unit


class ApplyForm(forms.Form):
    facility = forms.ModelChoiceField(queryset=Facility.objects.filter(is_active=True))
    unit = forms.ModelChoiceField(queryset=Unit.objects.none())
    category = forms.ChoiceField(choices=[
        ('government', 'Government official'),
        ('citizen', 'Public citizen'),
        ('organization', 'Organization'),
    ])
    check_in = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    check_out = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    slot = forms.ChoiceField(required=False, choices=SLOT_CHOICES)
    guests = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        facility = None
        if self.is_bound:
            try:
                facility_id = int(self.data.get('facility') or 0)
                facility = Facility.objects.filter(pk=facility_id).first()
            except (TypeError, ValueError):
                facility = None
        elif self.initial.get('facility'):
            facility = self.initial['facility']
        if facility is None:
            unit_qs = Unit.objects.filter(is_active=True)
        else:
            unit_qs = facility.units.filter(is_active=True)
        self.fields['unit'].queryset = unit_qs.select_related('facility')

    def clean(self):
        data = super().clean()
        unit = data.get('unit')
        check_in = data.get('check_in')
        check_out = data.get('check_out')
        category = data.get('category')
        slot = data.get('slot') or ''
        if not unit or not check_in or not check_out:
            return data

        today = timezone.localdate()
        notice_days = max(1, round(get_int('min_notice_hours', 24) / 24) or 1)
        earliest = today + timedelta(days=notice_days - 1)
        if check_in < earliest:
            self.add_error('check_in', f'Check-in must be on or after {earliest:%d %b %Y}.')
        max_advance = get_int('advance_booking_days', 90)
        if check_in > today + timedelta(days=max_advance):
            self.add_error('check_in', f'Bookings open only {max_advance} days ahead.')

        if unit.is_hall:
            if not slot:
                self.add_error('slot', 'Choose a morning, afternoon or evening slot for the hall.')
            if check_out != check_in + timedelta(days=1):
                check_out = check_in + timedelta(days=1)
                data['check_out'] = check_out
            guests = data.get('guests') or 1
            if guests > unit.capacity:
                self.add_error('guests', f'This hall seats {unit.capacity} guests.')
        else:
            slot = ''
            if check_out <= check_in:
                self.add_error('check_out', 'Check-out must be after check-in.')
            nights = (check_out - check_in).days
            max_nights = get_int('max_nights', 14)
            if nights > max_nights:
                self.add_error('check_out', f'Maximum stay is {max_nights} nights.')
            if data.get('guests') and data['guests'] > get_int('max_guests', 12):
                self.add_error('guests', 'Too many guests for one application.')

        if data.get('facility') and unit.facility_id != data['facility'].pk:
            self.add_error('unit', 'That room belongs to a different facility.')
        if category and unit and tariff_for(unit, category) is None:
            self.add_error('category', 'No published tariff for this category and unit.')

        if not self.errors and check_in and check_out:
            if not is_free(unit, check_in, check_out, slot):
                self.add_error('unit', 'That room or slot is no longer available for the selected dates.')
        return data


class DetailsForm(forms.Form):
    purpose = forms.CharField(max_length=255, widget=forms.TextInput(
        attrs={'placeholder': 'Purpose of the visit or meeting'}))
    guests = forms.IntegerField(min_value=1, initial=1)
    contact_phone = forms.CharField(max_length=30, required=False)
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    terms = forms.BooleanField(
        label='I have read and accept the published terms, tariff and sample cancellation policy.')
