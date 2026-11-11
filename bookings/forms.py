from datetime import timedelta

from django import forms
from django.utils import timezone

from core.i18n import CURRENT_LANG, localize
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

    def __init__(self, *args, asset_category=None, **kwargs):
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
        if asset_category:
            unit_qs = unit_qs.filter(asset_category=asset_category)
        self.fields['unit'].queryset = unit_qs.select_related('facility')

    def _bn(self):
        return CURRENT_LANG.get() == 'bn'

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
            self.add_error('check_in', localize(f'চেক-ইন {earliest:%d %b %Y} বা তার পরে হতে হবে।')
                           if self._bn() else f'Check-in must be on or after {earliest:%d %b %Y}.')
        max_advance = get_int('advance_booking_days', 90)
        if check_in > today + timedelta(days=max_advance):
            self.add_error('check_in', localize(f'বুকিং শুধু {max_advance} দিন আগে পর্যন্ত খোলা।')
                           if self._bn() else f'Bookings open only {max_advance} days ahead.')

        if unit.is_hall:
            if not slot:
                self.add_error('slot', 'হলের জন্য সকাল, দুপুর বা সন্ধ্যার স্লট বেছে নিন।'
                               if self._bn() else 'Choose a morning, afternoon or evening slot for the hall.')
            if check_out != check_in + timedelta(days=1):
                check_out = check_in + timedelta(days=1)
                data['check_out'] = check_out
            guests = data.get('guests') or 1
            if guests > unit.capacity:
                self.add_error('guests', localize(f'এই হলে সর্বোচ্চ {unit.capacity} জন অতিথির স্থান আছে।')
                               if self._bn() else f'This hall seats {unit.capacity} guests.')
        else:
            slot = ''
            if check_out <= check_in:
                self.add_error('check_out', 'চেক-আউট চেক-ইনের পরে হতে হবে।'
                               if self._bn() else 'Check-out must be after check-in.')
            nights = (check_out - check_in).days
            max_nights = get_int('max_nights', 14)
            if nights > max_nights:
                self.add_error('check_out', localize(f'সর্বোচ্চ অবস্থান {max_nights} রাত।')
                               if self._bn() else f'Maximum stay is {max_nights} nights.')
            if data.get('guests') and data['guests'] > get_int('max_guests', 12):
                self.add_error('guests', 'একটি আবেদনে অতিথির সংখ্যা বেশি হয়ে গেছে।'
                               if self._bn() else 'Too many guests for one application.')

        if data.get('guests') and data['guests'] > unit.capacity:
            self.add_error('guests', 'The number of guests exceeds the selected asset capacity.')

        if data.get('facility') and unit.facility_id != data['facility'].pk:
            self.add_error('unit', 'এই কক্ষটি অন্য একটি সুবিধার অন্তর্গত।'
                           if self._bn() else 'That room belongs to a different facility.')
        if category and unit and tariff_for(unit, category) is None:
            self.add_error('category', 'এই শ্রেণি ও কক্ষের জন্য কোনো প্রকাশিত শুল্ক নেই।'
                           if self._bn() else 'No published tariff for this category and unit.')

        if not self.errors and check_in and check_out:
            if not is_free(unit, check_in, check_out, slot):
                self.add_error('unit', 'নির্বাচিত তারিখে এই কক্ষ বা স্লট আর পাওয়া যাচ্ছে না।'
                               if self._bn() else 'That room or slot is no longer available for the selected dates.')
        return data


class DetailsForm(forms.Form):
    purpose = forms.CharField(max_length=255, widget=forms.TextInput(
        attrs={'placeholder': 'Purpose of the visit or meeting'}))
    guests = forms.IntegerField(min_value=1, initial=1)
    contact_phone = forms.CharField(max_length=30, required=False)
    national_id = forms.CharField(max_length=40, required=False, widget=forms.TextInput(
        attrs={'inputmode': 'numeric', 'autocomplete': 'off'}))
    office_id = forms.CharField(max_length=40, required=False, widget=forms.TextInput(
        attrs={'autocomplete': 'off'}))
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'rows': 3}))
    terms = forms.BooleanField(
        label='I have read and accept the published terms, tariff and sample cancellation policy.')

    def __init__(self, *args, category='citizen', **kwargs):
        super().__init__(*args, **kwargs)
        self.category = category

    def clean_national_id(self):
        value = (self.cleaned_data.get('national_id') or '').strip().replace(' ', '')
        if value and not (value.isdigit() and 10 <= len(value) <= 17):
            raise forms.ValidationError(
                'A NID must be 10 to 17 digits (sample number only).')
        return value

    def clean(self):
        data = super().clean()
        national_id = data.get('national_id') or ''
        office_id = (data.get('office_id') or '').strip()
        if self.category == 'government':
            if not national_id and not office_id:
                raise forms.ValidationError(
                    'Government officials must give a NID or an office ID.')
        elif not national_id:
            self.add_error(
                'national_id',
                'A national ID (NID) is required to apply as a public citizen or organization.')
        return data
