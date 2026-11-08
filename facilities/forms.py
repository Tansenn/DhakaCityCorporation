from django import forms

from facilities.models import BlackoutDate, Facility, Tariff, Unit


class FacilityForm(forms.ModelForm):
    class Meta:
        model = Facility
        fields = ['name', 'description', 'location', 'amenities', 'rules',
                  'booking_types', 'contact', 'photo', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'rules': forms.Textarea(attrs={'rows': 3}),
            'amenities': forms.TextInput(),
            'booking_types': forms.TextInput(),
        }


class UnitForm(forms.ModelForm):
    class Meta:
        model = Unit
        fields = ['code', 'name', 'kind', 'capacity', 'description', 'amenities',
                  'is_active']
        widgets = {'description': forms.TextInput()}


class TariffForm(forms.ModelForm):
    class Meta:
        model = Tariff
        fields = ['unit', 'category', 'amount', 'holiday_amount', 'deposit']

    def __init__(self, *args, facility=None, **kwargs):
        super().__init__(*args, **kwargs)
        if facility is not None:
            self.fields['unit'].queryset = facility.units.all()


class BlackoutForm(forms.ModelForm):
    class Meta:
        model = BlackoutDate
        fields = ['date', 'reason']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}
