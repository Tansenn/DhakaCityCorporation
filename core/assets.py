from datetime import timedelta

ASSETS = [
    {'code': 'land', 'name': 'Lands', 'icon': 'bi-map', 'unit': 'plots',
     'headline': 'Room for your next idea.', 'intro': 'Find open spaces for your next community activity.'},
    {'code': 'ponds', 'name': 'Ponds', 'icon': 'bi-water', 'unit': 'ponds',
     'headline': 'A little closer to nature.', 'intro': 'Explore peaceful waterside spaces across Gazipur.'},
    {'code': 'markets', 'name': 'Markets', 'icon': 'bi-shop', 'unit': 'stalls',
     'headline': 'A place for local enterprise.', 'intro': 'Discover market spaces and plan your next trading day.'},
    {'code': 'kheyaghat', 'name': 'Kheyaghat', 'icon': 'bi-signpost-2', 'unit': 'ghats',
     'headline': 'Connect with the riverside.', 'intro': 'Browse ferry-ghat spaces and check available dates.'},
    {'code': 'auditorium', 'name': 'Auditorium', 'icon': 'bi-mic', 'unit': 'halls',
     'headline': 'Bring everyone together.', 'intro': 'Find a welcoming space for meetings, events and celebrations.'},
    {'code': 'dakbungalow', 'name': 'Dakbungalows', 'icon': 'bi-house-door', 'unit': 'units',
     'headline': 'A quieter stay in Gazipur.', 'intro': 'Four dakbungalows. One simple way to find your stay.'},
]
for asset in ASSETS:
    asset['image'] = f"img/asset-{asset['code']}.jpg"
    asset['detail'] = 'Sample inventory'


def asset_status(day):
    from facilities.availability import is_free
    from facilities.models import Unit

    units = list(Unit.objects.filter(is_active=True, facility__is_active=True))
    rows = []
    for asset in ASSETS:
        group = [unit for unit in units if unit.asset_category == asset['code']]
        free = sum(is_free(unit, day, day + timedelta(days=1),
                           'morning' if unit.is_hall else '') for unit in group)
        total = len(group)
        rows.append({**asset, 'total': total, 'free': free, 'booked': total - free,
                     'percent': round((total - free) * 100 / total) if total else 0})
    return rows
