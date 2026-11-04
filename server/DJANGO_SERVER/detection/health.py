import time
import urllib.request

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

from parking.interface import supervised_parkings
from shared.hours import is_open
from . import state
from .worker import parking_time

ALERT_AFTER = 120
LAST_ALERT_KEY = 'health:last_alert'


def model_server_up():
    try:
        with urllib.request.urlopen(f"{settings.MODEL_SERVER_URL}/health", timeout=3) as response:
            return response.status == 200
    except OSError:
        return False


def zone_health(parking_id, area, now):
    current = state.latest(parking_id, area)
    age = None if current is None else round(now - current['ts'])
    camera_down = current is not None and current['total'] and current['errors'] == current['total']
    return {
        'area': area,
        'age': age,
        'free': None if state.is_stale(current, now) else current['available_spots'],
        'total': current['total'] if current else None,
        'ok': not state.is_stale(current, now),
        'late': current is None or age > ALERT_AFTER or bool(camera_down),
    }


def report():
    now = time.time()
    local = parking_time()
    parkings = []
    problems = []
    model_up = model_server_up()
    if not model_up:
        problems.append("Serveur du modèle injoignable")
    for parking in supervised_parkings():
        is_open_now = is_open(parking['opening_hours'], local)
        zones = [zone_health(parking['id'], area, now) for area in parking['areas']]
        parkings.append({**parking, 'open': is_open_now, 'zones': zones})
        if parking['visible'] and is_open_now:
            for zone in zones:
                if zone['late']:
                    waited = "aucune donnée" if zone['age'] is None else f"dernière donnée il y a {zone['age']} s"
                    problems.append(f"{parking['name']}, zone {zone['area']} : {waited}")
    return {'model_up': model_up, 'parkings': parkings, 'problems': problems}


def alert(problems):
    last = cache.get(LAST_ALERT_KEY, [])
    if problems == last:
        return False
    if problems:
        subject = f"Supervision : {len(problems)} problème(s)"
        body = "\n".join(f"- {p}" for p in problems)
    else:
        subject = "Supervision : tout est rétabli"
        body = "Plus aucun problème détecté."
    send_mail(subject, body, None, [settings.TEAM_EMAIL], fail_silently=False)
    cache.set(LAST_ALERT_KEY, problems, None)
    return True
