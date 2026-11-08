from __future__ import annotations

import csv
import io
import re
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.core.exceptions import ValidationError
from django.http import HttpResponse
from django.utils import timezone


def now():
    return timezone.now()


def today():
    return timezone.localdate()


def money(value, symbol='৳'):
    try:
        amount = Decimal(str(value or 0))
    except (InvalidOperation, TypeError, ValueError):
        amount = Decimal('0')
    return f'{symbol}{amount:,.2f}'


def parse_date(value, default=None):
    if isinstance(value, date):
        return value
    if not value:
        return default
    for fmt in ('%Y-%m-%d', '%d/%m/%Y', '%d-%m-%Y'):
        try:
            return datetime.strptime(str(value).strip(), fmt).date()
        except ValueError:
            continue
    return default


def parse_decimal(value, default='0'):
    try:
        return Decimal(str(value).strip().replace(',', ''))
    except (InvalidOperation, AttributeError, TypeError):
        return Decimal(str(default))


def get_client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    if forwarded:
        return forwarded.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '0.0.0.0')


def validate_upload(upload, label='File'):
    """Type + size checks for every uploaded document."""
    if upload is None:
        return upload
    max_bytes = settings.UPLOAD_MAX_MB * 1024 * 1024
    if upload.size > max_bytes:
        raise ValidationError(
            f'{label}: file is larger than {settings.UPLOAD_MAX_MB} MB.'
        )
    name = (upload.name or '').lower()
    ext = '.' + name.rsplit('.', 1)[-1] if '.' in name else ''
    if ext not in settings.UPLOAD_ALLOWED_EXT:
        allowed = ', '.join(sorted(settings.UPLOAD_ALLOWED_EXT))
        raise ValidationError(f'{label}: allowed file types are {allowed}.')
    return upload


def safe_filename(name):
    return re.sub(r'[^A-Za-z0-9._-]', '_', name or 'file')


def is_ajax(request):
    return request.headers.get('x-requested-with') == 'XMLHttpRequest'


def csv_response(filename, headers, rows):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    response.write('\ufeff')
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response


def business_hours_after(start, hours):
    """Simple acknowledgement deadline: add business hours (Mon-Fri 09:00-17:00)."""
    current = start
    remaining = Decimal(str(hours)) * 60
    while remaining > 0:
        if current.weekday() < 5:
            current += timedelta(minutes=min(60, remaining))
            remaining -= 60
        else:
            current = start.replace(hour=9, minute=0) + timedelta(
                days=(7 - current.weekday()) % 7 or 7
            )
            remaining -= 60
        if current.hour >= 17:
            current = (current + timedelta(days=1)).replace(hour=9, minute=0)
            if current.weekday() >= 5:
                current = current + timedelta(days=(7 - current.weekday()))
    return current


def next_reference(prefix, model, field, width=6):
    """Build a sequential reference like GZP-DB-2026-000123."""
    year = today().year
    pattern = f'{prefix}-{year}-'
    last = (
        model.objects.filter(**{f'{field}__startswith': pattern})
        .order_by(f'-{field}')
        .values_list(field, flat=True)
        .first()
    )
    seq = 1
    if last:
        try:
            seq = int(str(last).split('-')[-1]) + 1
        except ValueError:
            seq = model.objects.filter(**{f'{field}__startswith': pattern}).count() + 1
    return f'{pattern}{seq:0{width}d}'


def parse_int(value, default=0):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def daterange_days(start, end):
    if not start or not end:
        return []
    out = []
    current = start
    while current < end:
        out.append(current)
        current += timedelta(days=1)
    return out


def month_bounds(anchor=None):
    anchor = anchor or today()
    start = anchor.replace(day=1)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1, day=1)
    else:
        end = start.replace(month=start.month + 1, day=1)
    return start, end


def human_duration(td):
    if not td:
        return '-'
    total = int(td.total_seconds())
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    if days:
        return f'{days}d {hours}h'
    if hours:
        return f'{hours}h {minutes}m'
    return f'{minutes}m'


def read_csv_rows(upload, max_rows=2000):
    raw = upload.read()
    try:
        text = raw.decode('utf-8-sig')
    except UnicodeDecodeError:
        text = raw.decode('latin-1')
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for i, row in enumerate(reader):
        if i >= max_rows:
            break
        rows.append(row)
    return rows


def clamp(value, low=None, high=None):
    if low is not None and value < low:
        value = low
    if high is not None and value > high:
        value = high
    return value


def initials(name):
    parts = [p for p in (name or '').split() if p]
    return ''.join(p[0].upper() for p in parts[:2]) or '?'


def paginate(request, queryset, per_page=25):
    from django.core.paginator import Paginator

    paginator = Paginator(queryset, per_page)
    return paginator.get_page(request.GET.get('page'))
