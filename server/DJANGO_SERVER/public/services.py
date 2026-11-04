import logging
from datetime import datetime, timezone

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from detection.interface import parking_availability
from parking.interface import published_parking, published_parkings_in_box
from shared.geo import bounding_box, distance_m

MAX_RESULTS = 20
FAILED_LOGIN_LIMIT = 5
FAILED_LOGIN_WINDOW = 60
ACCOUNT_FAILURE_LIMIT = 30
ACCOUNT_FAILURE_WINDOW = 15 * 60
KNOWN_ADDRESS_TTL = 30 * 24 * 3600

logger = logging.getLogger(__name__)


def mail_team(subject, fields):
    body = "\n".join(f"{label} : {value}" for label, value in fields if value not in (None, ''))
    send_mail(subject, body, settings.EMAIL_HOST_USER, [settings.TEAM_EMAIL], fail_silently=False)


def submit_owner_request(serializer):
    request = serializer.save()
    fields = [(f.verbose_name, getattr(request, f.name)) for f in request._meta.fields if f.name not in ('id', 'status')]
    try:
        mail_team(f"Inscription d'un parking : {request.parking_name}", fields)
    except Exception:
        logger.exception("Owner request %s saved but the team e-mail failed", request.pk)
    return request


def send_contact(data):
    mail_team("Message du site", [('Nom', data['name']), ('E-mail', data['email']), ('Message', data['message'])])


def iso(timestamp):
    if timestamp is None:
        return None
    return datetime.fromtimestamp(timestamp, tz=timezone.utc).isoformat().replace('+00:00', 'Z')


def availability(parking):
    state = parking_availability(parking['id'], parking['areas'])
    return {
        'free': state['free'],
        'total': state['total'] if not state['stale'] else (parking['capacity'] or None),
        'updated_at': iso(state['updated_at']),
        'stale': state['stale'],
    }


def summary(parking):
    return {
        'id': str(parking['id']),
        'name': parking['name'],
        'address': parking['address'],
        'latitude': parking['latitude'],
        'longitude': parking['longitude'],
    }


def nearby(lat, lng, radius_m):
    found = []
    for parking in published_parkings_in_box(*bounding_box(lat, lng, radius_m)):
        distance = distance_m(lat, lng, parking['latitude'], parking['longitude'])
        if distance <= radius_m:
            found.append((distance, parking))
    found.sort(key=lambda item: item[0])
    return [
        {**summary(p), 'distance_m': distance, **availability(p)}
        for distance, p in found[:MAX_RESULTS]
    ]


def detail(parking_id):
    parking = published_parking(parking_id)
    if parking is None:
        return None
    return {
        **summary(parking),
        'capacity': parking['capacity'],
        'opening_hours': parking['opening_hours'],
        'pricing_text': parking['pricing_text'],
        **availability(parking),
    }


def account(username):
    return username.strip().lower()


def failure_key(username, client):
    return f"login_failures:{account(username)}:{client}"


def account_failure_key(username):
    return f"login_failures:{account(username)}"


def known_address_key(username, client):
    return f"login_known:{account(username)}:{client}"


def attempt(key, window):
    if cache.add(key, 1, window):
        return 1
    try:
        return cache.incr(key)
    except ValueError:
        cache.set(key, 1, window)
        return 1


def start_login(username, client):
    per_address = attempt(failure_key(username, client), FAILED_LOGIN_WINDOW)
    per_account = attempt(account_failure_key(username), ACCOUNT_FAILURE_WINDOW)
    if per_address > FAILED_LOGIN_LIMIT:
        return False
    if per_account > ACCOUNT_FAILURE_LIMIT:
        return bool(cache.get(known_address_key(username, client)))
    return True


def login_succeeded(username, client):
    cache.delete(failure_key(username, client))
    try:
        cache.decr(account_failure_key(username))
    except ValueError:
        pass
    cache.set(known_address_key(username, client), True, KNOWN_ADDRESS_TTL)
