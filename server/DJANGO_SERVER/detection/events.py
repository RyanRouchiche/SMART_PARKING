from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer


def zone_group(parking_id, area):
    return f"zone_{parking_id}_{area}"


def occupancy_message(area, names, statuses):
    return {
        'area': area,
        'available_spots': statuses.count('empty'),
        'spot_details': [{'spot': n, 'status': s} for n, s in zip(names, statuses)],
    }


def publish(parking_id, area, message):
    async_to_sync(get_channel_layer().group_send)(
        zone_group(parking_id, area), {'type': 'zone.occupancy', 'message': message}
    )
