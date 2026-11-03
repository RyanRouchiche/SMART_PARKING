from django.db import transaction

from users.interface import delete_account, send_activation_email
from .models import ParkingMembership, Zone


def zone_layouts(parking):
    return [{'area': str(z.number), 'coordinates': z.spots} for z in parking.zones.all()]


def zone_numbers(parking):
    return list(parking.zones.values_list('number', flat=True))


def save_zone_spots(parking, number, spots, camera_id):
    Zone.objects.update_or_create(
        parking=parking,
        number=number,
        defaults={'spots': spots, 'camera_id': camera_id},
    )


def all_zone_layouts():
    return [(z.parking_id, z.number, z.spots) for z in Zone.objects.exclude(spots={})]


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
