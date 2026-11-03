import time

from django.core.cache import cache

STALE_AFTER = 15
STATE_TTL = 120
MESSAGE_FIELDS = ('area', 'available_spots', 'spot_details')


def state_key(parking_id, area):
    return f"availability:{parking_id}:{area}"


def build(message, now=None):
    statuses = [d['status'] for d in message['spot_details']]
    return {
        **message,
        'total': len(statuses),
        'errors': statuses.count('error'),
        'ts': time.time() if now is None else now,
    }


def store(parking_id, area, message, now=None):
    state = build(message, now)
    cache.set(state_key(parking_id, area), state, STATE_TTL)
    return state


def latest(parking_id, area):
    return cache.get(state_key(parking_id, area))


def is_stale(state, now=None):
    if state is None or (state['total'] and state['errors'] == state['total']):
        return True
    return (time.time() if now is None else now) - state['ts'] > STALE_AFTER


def public_message(state):
    return {field: state[field] for field in MESSAGE_FIELDS}


def parking_availability(parking_id, areas, now=None):
    states = cache.get_many([state_key(parking_id, a) for a in areas])
    zones = []
    for area in areas:
        state = states.get(state_key(parking_id, area))
        stale = is_stale(state, now)
        zones.append({
            'area': area,
            'free': None if stale else state['available_spots'],
            'total': state['total'] if state else None,
            'updated_at': state['ts'] if state else None,
            'stale': stale,
        })
    fresh = [z for z in zones if not z['stale']]
    return {
        'free': sum(z['free'] for z in fresh) if fresh else None,
        'total': sum(z['total'] for z in fresh) if fresh else None,
        'updated_at': min(z['updated_at'] for z in fresh) if fresh else None,
        'stale': not fresh,
        'zones': zones,
    }
