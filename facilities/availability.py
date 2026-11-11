"""Availability, temporary holds and conflict prevention.

Inventory is locked per night for rooms/suites and per date+slot for halls. A
partial unique constraint in the database guarantees that two active locks can
never exist for the same inventory item, so concurrent bookings cannot collide.
"""
from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from core.i18n import CURRENT_LANG, localize, translate
from core.models import get_bool, get_decimal, get_int
from facilities.models import BlackoutDate, InventoryLock, Tariff, Unit

HALL_SLOTS = ['morning', 'afternoon', 'evening']
SLOT_CHOICES = [
    ('', 'Full day / overnight'),
    ('morning', 'Morning (09:00-13:00)'),
    ('afternoon', 'Afternoon (13:00-17:00)'),
    ('evening', 'Evening (17:00-21:00)'),
]


def release_expired_holds(units=None):
    now = timezone.now()
    qs = InventoryLock.objects.filter(
        released=False, hold_expires_at__isnull=False, hold_expires_at__lte=now
    )
    if units is not None:
        qs = qs.filter(unit__in=units)
    return qs.update(released=True)


def active_lock_filter(now=None):
    now = now or timezone.now()
    return Q(hold_expires_at__isnull=True) | Q(hold_expires_at__gt=now)


def active_locks(unit, start=None, end=None, slot=None):
    qs = InventoryLock.objects.filter(unit=unit, released=False).filter(active_lock_filter())
    if start:
        qs = qs.filter(date__gte=start)
    if end:
        qs = qs.filter(date__lt=end)
    if slot is not None:
        qs = qs.filter(slot=slot)
    return qs


def booked_dates(unit, start, end, slot=''):
    """Dates in [start, end) that are already taken for the given slot mode."""
    qs = active_locks(unit, start, end)
    if unit.is_hall:
        qs = qs.filter(slot=slot)
    else:
        qs = qs.filter(slot='')
    return set(qs.values_list('date', flat=True))


def is_free(unit, start, end, slot=''):
    if unit.is_hall:
        if start != end and (end - start).days > 1:
            return False
        return not active_locks(unit, start, start + timedelta(days=1), slot).exists()
    taken = booked_dates(unit, start, end)
    return not taken


def blackout_dates(facility, start, end):
    return set(
        BlackoutDate.objects.filter(
            facility=facility, date__gte=start, date__lt=end
        ).values_list('date', flat=True)
    )


def available_units(facility, start, end, slot=''):
    units = list(facility.units.filter(is_active=True, asset_category='dakbungalow'))
    out = []
    for unit in units:
        if unit.is_hall and not slot:
            continue
        if is_free(unit, start, end, slot):
            out.append(unit)
    return out


def take_hold(unit, dates, slot, hold_until, booking=None):
    """Create the inventory locks. Raises IntegrityError when already taken."""
    created = []
    try:
        for day in dates:
            created.append(InventoryLock.objects.create(
                unit=unit, date=day, slot=slot, booking=booking,
                hold_expires_at=hold_until,
            ))
    except IntegrityError:
        for lock in created:
            lock.delete()
        raise
    return created


def confirm_locks(booking, until=None):
    """Extend the booking's locks to the payment window or make them permanent."""
    booking.locks.filter(released=False).update(hold_expires_at=until)


def release_booking_locks(booking):
    return booking.locks.filter(released=False).update(released=True)


def resolve_payment_window(booking):
    hours = get_int('payment_window_hours', 24)
    return timezone.now() + timedelta(hours=hours)


def tariff_for(unit, category):
    return (unit.tariffs.filter(category=category).first()
            or unit.tariffs.filter(category='citizen').first())


def is_holiday(day):
    # Sample rule: Friday/Saturday weekend, labelled sample in the UI.
    return day.weekday() in (4, 5)


def _rate_label(day):
    holiday = is_holiday(day)
    if CURRENT_LANG.get() == 'bn':
        return 'ছুটির দিনের হার' if holiday else 'সাধারণ হার'
    return 'holiday rate' if holiday else 'standard rate'


def quote(unit, category, start, end, slot=''):
    """Return a transparent price breakdown. All values are sample settings."""
    tariff = tariff_for(unit, category)
    if tariff is None:
        return None
    lines = []
    charges = Decimal('0')
    deposit = tariff.deposit or Decimal('0')
    bn = CURRENT_LANG.get() == 'bn'

    if unit.is_hall:
        rate = tariff.holiday_amount if is_holiday(start) else tariff.amount
        nights = 1
        charges = rate
        slot_label = dict(SLOT_CHOICES).get(slot, 'Full day / overnight')
        if bn:
            slot_label = translate(slot_label, 'bn')
            label = f'কনফারেন্স হল - {slot_label} ({start.strftime("%d %b %Y")})'
        else:
            label = (f'Conference hall - {slot_label} on '
                     f'{start.strftime("%d %b %Y")}')
        lines.append({
            'label': localize(label),
            'amount': rate,
        })
    else:
        nights = (end - start).days
        day = start
        while day < end:
            rate = tariff.holiday_amount if is_holiday(day) else tariff.amount
            charges += rate
            lines.append({
                'label': localize(f'{day.strftime("%d %b %Y")} - {_rate_label(day)}'),
                'amount': rate,
            })
            day += timedelta(days=1)

    gateway_charge = Decimal('0')
    if get_bool('gateway_charge_paid_by_user', False):
        gateway_charge = get_decimal('gateway_charge_amount', '0')
    total = charges + deposit + gateway_charge
    return {
        'tariff': tariff,
        'unit': unit,
        'category': category,
        'nights': nights,
        'lines': lines,
        'charges': charges,
        'deposit': deposit,
        'gateway_charge': gateway_charge,
        'total': total,
        'slot': slot,
        'check_in': start,
        'check_out': end,
        'holiday_nights': sum(1 for line in lines if 'holiday' in line['label']),
    }


def refund_percent(days_before):
    """Parse the editable sample policy, e.g. '7:100,3:50,1:25,0:0'."""
    from core.models import get_setting

    raw = get_setting('refund_policy', '7:100,3:50,1:25,0:0')
    rules = []
    for part in raw.split(','):
        if ':' in part:
            try:
                rules.append((int(part.split(':')[0]), Decimal(part.split(':')[1])))
            except (ValueError, ArithmeticError):
                continue
    rules.sort(reverse=True)
    for threshold, percent in rules:
        if days_before >= threshold:
            return percent, raw
    return Decimal('0'), raw


def refund_policy_text():
    from core.models import get_setting

    raw = get_setting('refund_policy', '7:100,3:50,1:25,0:0')
    rules = []
    for part in raw.split(','):
        if ':' in part:
            try:
                rules.append((int(part.split(':')[0]), Decimal(part.split(':')[1])))
            except (ValueError, ArithmeticError):
                continue
    rules.sort(reverse=True)
    if CURRENT_LANG.get() == 'bn':
        bits = [f'চেক-ইনের {days}+ দিন আগে বাতিলে {int(percent)}% ফেরত'
                for days, percent in rules]
        return localize('; '.join(bits) + ' (নমুনা নীতি)')
    bits = [f'{int(percent)}% if cancelled {days}+ day(s) before check-in'
            for days, percent in rules]
    return '; '.join(bits) + ' (sample policy)'


def hold_hours():
    return get_int('hold_hours', 48)


def facility_calendar(facility, start, days=35, asset_category=None):
    """A simple availability grid: booked and free rooms per day."""
    from django.db.models import Count

    from core.utils import daterange_days

    end = start + timedelta(days=days)
    units_qs = facility.units.filter(is_active=True).exclude(kind='hall')
    locks_qs = InventoryLock.objects.filter(
        unit__facility=facility, released=False, date__gte=start, date__lt=end,
    ).filter(active_lock_filter()).exclude(unit__kind='hall')
    if asset_category:
        units_qs = units_qs.filter(asset_category=asset_category)
        locks_qs = locks_qs.filter(unit__asset_category=asset_category)
    room_count = units_qs.count()
    blackouts = blackout_dates(facility, start, end)
    rows = locks_qs.values('date').annotate(n=Count('id'))
    booked = {row['date']: row['n'] for row in rows}
    today_value = timezone.localdate()
    out = []
    for day in daterange_days(start, end):
        taken = booked.get(day, 0)
        out.append({
            'date': day,
            'booked': taken,
            'free': max(0, room_count - taken),
            'is_blackout': day in blackouts,
            'is_past': day < today_value,
            'is_today': day == today_value,
        })
    return out
