from django.db import transaction

from users.interface import delete_account, send_activation_email
from .models import Parking, ParkingMembership, Subscription, Zone


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
    zones = Zone.objects.exclude(spots={}).exclude(parking__subscription__status=Subscription.CANCELLED).select_related('parking')
    return [(z.parking_id, z.number, z.ordered_spots, z.parking.opening_hours) for z in zones]


PUBLIC_FIELDS = ('id', 'name', 'address', 'latitude', 'longitude', 'capacity', 'opening_hours', 'pricing_text')


def published_parkings():
    return (
        Parking.objects.filter(is_published=True, latitude__isnull=False, longitude__isnull=False)
        .filter(subscription__status__in=Subscription.VISIBLE)
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


def create_draft_parking(owner, name, address, capacity):
    with transaction.atomic():
        parking = Parking.objects.create(name=name, address=address, capacity=capacity)
        ParkingMembership.objects.create(user=owner, parking=parking, role=ParkingMembership.OWNER)
    return parking


def supervised_parkings():
    visible = set(published_parkings().values_list('pk', flat=True))
    parkings = (
        Parking.objects.exclude(subscription__status=Subscription.CANCELLED)
        .select_related('subscription')
        .prefetch_related('zones')
        .order_by('name')
    )
    return [
        {
            'id': p.pk,
            'name': p.name,
            'visible': p.pk in visible,
            'opening_hours': p.opening_hours,
            'areas': sorted(z.number for z in p.zones.all() if z.spots),
            'subscription': p.subscription.get_status_display(),
            'period_end': p.subscription.period_end,
        }
        for p in parkings
    ]


def published_parkings_with_ids(ids):
    return [public_parking(p) for p in published_parkings().filter(pk__in=ids).prefetch_related('zones')]
