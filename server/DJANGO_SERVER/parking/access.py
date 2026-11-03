from django.core.exceptions import ValidationError
from rest_framework.exceptions import PermissionDenied

from .models import Parking, ParkingMembership


def member_parkings(user, role=None):
    if not user.is_authenticated:
        return Parking.objects.none()
    memberships = ParkingMembership.objects.filter(user=user)
    if role:
        memberships = memberships.filter(role=role)
    return Parking.objects.filter(memberships__in=memberships).distinct()


def resolve_parking(user, parking_id=None, owner=False):
    parkings = member_parkings(user, ParkingMembership.OWNER if owner else None).order_by('created_at')
    try:
        parking = parkings.filter(pk=parking_id).first() if parking_id else parkings.first()
    except ValidationError:
        parking = None
    if parking is None:
        raise PermissionDenied("You do not have access to this parking")
    return parking


def get_parking(request, owner=False):
    return resolve_parking(request.user, request.query_params.get('parking'), owner)


def zone_stream(user, area, parking_id=None):
    try:
        parking = resolve_parking(user, parking_id)
    except PermissionDenied:
        return None
    zone = parking.zones.filter(number=area).exclude(spots={}).first()
    has_camera = parking.cameras.filter(area=area).exists()
    return parking.pk if zone and has_camera else None


def still_member(user_id, parking_id):
    return ParkingMembership.objects.filter(user_id=user_id, parking_id=parking_id, user__is_active=True).exists()
