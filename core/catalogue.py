from datetime import timedelta
from urllib.parse import urlencode

from django import forms
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

from bookings.forms import ApplyForm
from core.assets import ASSETS
from core.models import get_int
from facilities.availability import is_free, quote
from facilities.models import Unit


class SearchForm(forms.Form):
    asset = forms.ChoiceField(choices=[(row['code'], row['name']) for row in ASSETS])
    q = forms.CharField(required=False, max_length=120)
    check_in = forms.DateField()
    check_out = forms.DateField()
    guests = forms.IntegerField(min_value=1, max_value=400)
    slot = forms.ChoiceField(required=False, choices=[('', 'Full day'), ('morning', 'Morning'), ('afternoon', 'Afternoon'), ('evening', 'Evening')])
    sort = forms.ChoiceField(required=False, choices=[('', 'Recommended'), ('price', 'Price: low to high'), ('name', 'Name')])

    def clean(self):
        data = super().clean()
        start, end = data.get('check_in'), data.get('check_out')
        if start and end:
            if start < timezone.localdate():
                self.add_error('check_in', 'Choose today or a future date.')
            elif start > timezone.localdate() + timedelta(days=get_int('advance_booking_days', 90)):
                self.add_error('check_in', 'Choose a date within the booking window.')
            if end <= start or (end - start).days > get_int('max_nights', 14):
                self.add_error('check_out', 'Choose an end date after the start, within 14 days.')
        return data


def catalogue(request):
    day = timezone.localdate() + timedelta(days=1)
    values = {'asset': 'dakbungalow', 'q': '', 'check_in': day.isoformat(),
              'check_out': (day + timedelta(days=1)).isoformat(), 'guests': 1,
              'slot': 'morning', 'sort': ''}
    values.update({key: request.GET[key] for key in values if key in request.GET})
    form = SearchForm(values)
    selected = next((row for row in ASSETS if row['code'] == values['asset']), ASSETS[-1])
    cards = []
    if form.is_valid():
        data = form.cleaned_data
        units = Unit.objects.filter(is_active=True, facility__is_active=True,
                                    asset_category=data['asset'], capacity__gte=data['guests']).select_related('facility').prefetch_related('tariffs')
        if data['q']:
            units = units.filter(Q(name__icontains=data['q']) | Q(facility__name__icontains=data['q']) | Q(facility__location__icontains=data['q']))
        for item in units:
            slot = (data['slot'] or 'morning') if item.is_hall else ''
            end = data['check_in'] + timedelta(days=1) if item.is_hall else data['check_out']
            price = quote(item, 'citizen', data['check_in'], end, slot)
            if price is None:
                continue
            free = is_free(item, data['check_in'], end, slot)
            query = urlencode({'check_in': data['check_in'], 'check_out': end,
                               'guests': data['guests'], 'slot': slot,
                               'flow': 'approval_first' if request.GET.get('flow') == 'approval_first' else 'direct'})
            card = {'unit': item, 'title': item.facility.name if data['asset'] == 'dakbungalow' else item.name,
                    'location': item.facility.location, 'description': item.description,
                    'image': item.catalogue_image, 'available': free, 'price': price['total'],
                    'url': reverse('asset_detail', args=[item.pk]) + '?' + query,
                    'capacity': item.capacity}
            existing = next((row for row in cards if row['unit'].facility_id == item.facility_id), None) if data['asset'] == 'dakbungalow' else None
            if existing:
                if (free and not existing['available']) or (free == existing['available'] and card['price'] < existing['price']):
                    cards[cards.index(existing)] = card
            else:
                cards.append(card)
        if data['sort'] == 'price':
            cards.sort(key=lambda card: card['price'])
        elif data['sort'] == 'name':
            cards.sort(key=lambda card: card['title'])
        else:
            cards.sort(key=lambda card: not card['available'])
    return render(request, 'core/catalogue.html', {
        'selected_asset': selected, 'search': values, 'search_form': form, 'cards': cards,
        'page_title': 'User panel', 'is_catalogue': True,
        'minimum_date': timezone.localdate().isoformat(),
        'maximum_date': (timezone.localdate() + timedelta(days=get_int('advance_booking_days', 90))).isoformat(),
        'flow': 'approval_first' if request.GET.get('flow') == 'approval_first' else 'direct',
        'my_reservations': request.user.bookings.select_related('unit', 'facility')[:3] if request.user.is_authenticated and request.user.is_citizen else [],
    })


@require_http_methods(['GET', 'POST'])
def asset_detail(request, pk):
    item = get_object_or_404(Unit.objects.select_related('facility'), pk=pk, is_active=True, facility__is_active=True)
    choices = item.facility.units.filter(is_active=True, asset_category='dakbungalow') if item.asset_category == 'dakbungalow' else Unit.objects.filter(pk=item.pk)
    values = request.POST if request.method == 'POST' else request.GET
    flow = 'approval_first' if values.get('flow') == 'approval_first' else 'direct'
    day = timezone.localdate() + timedelta(days=1)
    initial = {'facility': item.facility, 'unit': item.pk, 'category': 'citizen',
               'check_in': values.get('check_in', day.isoformat()),
               'check_out': values.get('check_out', (day + timedelta(days=1)).isoformat()),
               'guests': values.get('guests', 1), 'slot': values.get('slot') or ('morning' if item.is_hall else '')}
    if request.method == 'POST':
        if not request.user.is_authenticated:
            query = urlencode({key: values.get(key, '') for key in ('check_in', 'check_out', 'guests', 'slot', 'flow')})
            return redirect('/login/?portal=user&next=' + urlencode({'x': request.path + '?' + query})[2:])
        if not request.user.is_citizen:
            raise PermissionDenied('Use a citizen account to make a reservation.')
        form = ApplyForm(request.POST)
        form.fields['unit'].queryset = choices
        if form.is_valid():
            data = form.cleaned_data
            chosen = data['unit']
            request.session['booking_draft'] = {
                'facility_id': chosen.facility_id, 'unit_id': chosen.pk, 'category': data['category'],
                'check_in': data['check_in'].isoformat(), 'check_out': data['check_out'].isoformat(),
                'slot': data['slot'] if chosen.is_hall else '', 'guests': data['guests'],
                'payment_flow': flow,
            }
            return redirect('apply_details')
    else:
        form = ApplyForm(initial=initial)
    return render(request, 'core/asset_detail.html', {
        'unit': item, 'facility': item.facility, 'units': choices.prefetch_related('tariffs'),
        'form': form, 'flow': flow, 'page_title': item.name,
        'selected_asset': next(row for row in ASSETS if row['code'] == item.asset_category),
        'minimum_date': timezone.localdate().isoformat(),
    })
