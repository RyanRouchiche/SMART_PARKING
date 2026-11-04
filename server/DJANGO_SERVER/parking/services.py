from django.db import transaction

from users.interface import delete_account, send_activation_email
from .models import Parking, ParkingMembership, Zone


def zone_layouts(parking):
    return [{'area': str(z.number), 'coordinates': z.ordered_spots} for z in parking.zones.all()]


def zone_numbers(parking):
    return list(parking.zones.values_list('number', flat=True))


def save_zone_spots(parking, number, spots, camera_id):
    Zone.objects.update_or_create(
        parking=parking,
        number=number,
        defaults={'spots': spots, 'camera_id': camera_id},
    )


def all_zone_layouts():
    zones = Zone.objects.exclude(spots={}).select_related('parking')
    return [(z.parking_id, z.number, z.ordered_spots, z.parking.opening_hours) for z in zones]


PUBLIC_FIELDS = ('id', 'name', 'address', 'latitude', 'longitude', 'capacity', 'opening_hours', 'pricing_text')


def published_parkings():
    return (
        Parking.objects.filter(is_published=True, latitude__isnull=False, longitude__isnull=False)
        .filter(zones__in=Zone.objects.exclude(spots={}))
        .distinct()
    )


def public_parking(parking):
    return {
        **{field: getattr(parking, field) for field in PUBLIC_FIELDS},
        'areas': sorted({z.number for z in parking.zones.all() if z.spots}),
    }


def published_parkings_in_box(lat_min, lat_max, lng_min, lng_max):
    parkings = published_parkings().filter(
        latitude__range=(lat_min, lat_max), longitude__range=(lng_min, lng_max)
    ).prefetch_related('zones')
    return [public_parking(p) for p in parkings]


def published_parking(parking_id):
    parking = published_parkings().prefetch_related('zones').filter(pk=parking_id).first()
    return public_parking(parking) if parking else None


def operator_ids(parking):
    return ParkingMembership.objects.filter(parking=parking, role=ParkingMembership.OPERATOR).values_list('user_id', flat=True)


def add_operator(serializer, parking, request):
    with transaction.atomic():
        operator = serializer.save()
        ParkingMembership.objects.create(user=operator, parking=parking, role=ParkingMembership.OPERATOR)
    send_activation_email(request, operator)


def remove_operator(user_id, owned):
    memberships = ParkingMembership.objects.filter(user_id=user_id)
    removable = memberships.filter(parking__in=owned, role=ParkingMembership.OPERATOR)
    if not removable.exists() or memberships.filter(role=ParkingMembership.OWNER).exists():
        return False
    with transaction.atomic():
        removable.delete()
        if not memberships.exists():
            delete_account(user_id)
    return True
