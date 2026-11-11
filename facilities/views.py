from __future__ import annotations

from datetime import timedelta

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from accounts.decorators import perm_required
from audit.models import log
from core.assets import ASSETS
from core.utils import today, validate_upload
from facilities import availability
from facilities.forms import BlackoutForm, FacilityForm, TariffForm, UnitForm
from facilities.models import BlackoutDate, Facility, InventoryLock, Tariff, Unit


@perm_required('facilities.view')
def facility_list(request):
    facilities = Facility.objects.prefetch_related(
        'units', 'units__tariffs', 'blackout_dates')
    cards = []
    for facility in facilities:
        calendar = availability.facility_calendar(facility, today(), 14)
        units = list(facility.units.filter(is_active=True).prefetch_related('tariffs'))
        for unit in units:
            unit.next_days = []
            for offset in range(7):
                day = today() + timedelta(days=offset)
                free = availability.is_free(unit, day, day + timedelta(days=1),
                                           'morning' if unit.is_hall else '')
                unit.next_days.append({'date': day, 'free': free})
        cards.append({'facility': facility, 'units': units, 'calendar': calendar})
    return render(request, 'facilities/list.html', {
        'cards': cards,
        'assets': ASSETS,
        'rest_houses': len(cards),
        'unit_count': sum(len(card['units']) for card in cards),
        'expired_holds': InventoryLock.objects.filter(
            released=False, hold_expires_at__lt=timezone.now()).count(),
        'page_title': 'Assets',
    })


@perm_required('facilities.view')
def facility_detail(request, pk):
    facility = get_object_or_404(
        Facility.objects.prefetch_related('units__tariffs', 'blackout_dates'), pk=pk)
    can_manage = request.user.can('facilities.manage')
    facility_form = FacilityForm(instance=facility)
    unit_form = UnitForm()
    tariff_form = TariffForm(facility=facility)
    blackout_form = BlackoutForm()

    if request.method == 'POST' and can_manage:
        action = request.POST.get('action', 'facility')
        if action == 'facility':
            facility_form = FacilityForm(request.POST, request.FILES, instance=facility)
            if facility_form.is_valid():
                photo = request.FILES.get('photo')
                if photo:
                    try:
                        validate_upload(photo, 'Photo')
                    except ValidationError as exc:
                        messages.error(request, '; '.join(exc.messages))
                        return redirect('facility_detail', pk=facility.pk)
                facility_form.save()
                log(request.user, 'update', facility, 'Facility details updated',
                    module='facilities')
                messages.success(request, 'Facility details saved.')
                return redirect('facility_detail', pk=facility.pk)
            messages.error(request, 'Check the facility form and try again.')
        elif action == 'unit':
            unit_form = UnitForm(request.POST)
            if unit_form.is_valid():
                unit = unit_form.save(commit=False)
                unit.facility = facility
                unit.save()
                log(request.user, 'create', unit, 'Unit added', module='facilities')
                messages.success(request, f'Unit "{unit.name}" added.')
                return redirect('facility_detail', pk=facility.pk)
            messages.error(request, 'The unit could not be saved. Check the code is unique.')
        elif action == 'tariff':
            tariff_form = TariffForm(request.POST, facility=facility)
            if tariff_form.is_valid():
                tariff = tariff_form.save()
                log(request.user, 'update', tariff, 'Tariff saved', module='facilities')
                messages.success(request, 'Tariff saved.')
                return redirect('facility_detail', pk=facility.pk)
            messages.error(request, 'The tariff could not be saved.')
        elif action == 'blackout':
            blackout_form = BlackoutForm(request.POST)
            if blackout_form.is_valid():
                blackout = blackout_form.save(commit=False)
                blackout.facility = facility
                try:
                    blackout.save()
                    messages.success(request, 'Blackout date added.')
                except Exception:
                    messages.error(request, 'That date is already a blackout date.')
                log(request.user, 'create', blackout, 'Blackout date added',
                    module='facilities')
                return redirect('facility_detail', pk=facility.pk)
        elif action == 'delete_blackout':
            BlackoutDate.objects.filter(pk=request.POST.get('blackout'),
                                        facility=facility).delete()
            messages.success(request, 'Blackout date removed.')
            return redirect('facility_detail', pk=facility.pk)

    return render(request, 'facilities/detail.html', {
        'facility': facility,
        'units': facility.units.prefetch_related('tariffs'),
        'tariffs': Tariff.objects.filter(unit__facility=facility).select_related(
            'unit').order_by('unit__name', 'category'),
        'blackouts': facility.blackout_dates.order_by('date'),
        'calendar': availability.facility_calendar(facility, today(), 35),
        'calendar_leading': list(range(today().weekday())),
        'facility_form': facility_form,
        'unit_form': unit_form,
        'tariff_form': tariff_form,
        'blackout_form': blackout_form,
        'can_manage': can_manage,
        'page_title': facility.name,
    })


@require_POST
@perm_required('facilities.manage')
def delete_unit(request, pk):
    unit = get_object_or_404(Unit, pk=pk)
    facility_pk = unit.facility_id
    if unit.bookings.exclude(status__in=['cancelled', 'rejected', 'expired']).exists():
        unit.is_active = False
        unit.save(update_fields=['is_active'])
        messages.warning(request, 'The unit has booking history, so it was deactivated '
                                  'instead of deleted.')
    else:
        unit.delete()
        messages.success(request, 'Unit deleted.')
    log(request.user, 'delete', unit, 'Unit removed', module='facilities')
    return redirect('facility_detail', pk=facility_pk)


@require_POST
@perm_required('facilities.manage')
def delete_tariff(request, pk):
    tariff = get_object_or_404(Tariff, pk=pk)
    facility_pk = tariff.unit.facility_id
    tariff.delete()
    messages.success(request, 'Tariff removed.')
    return redirect('facility_detail', pk=facility_pk)


@require_POST
@perm_required('facilities.manage')
def release_holds(request):
    count = availability.release_expired_holds()
    messages.success(request, f'{count} expired hold(s) released.')
    log(request.user, 'update', None, f'{count} expired holds released',
        module='facilities')
    return redirect(request.POST.get('next') or 'facility_list')
