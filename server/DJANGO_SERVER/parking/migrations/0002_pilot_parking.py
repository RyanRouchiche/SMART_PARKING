import json
from pathlib import Path

from django.conf import settings
from django.db import migrations

PILOT_NAME = "Parking pilote"
COORDINATES_FILE = Path(settings.BASE_DIR) / "parking" / "Spots" / "coordinates.json"


def read_coordinates(path=COORDINATES_FILE):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def build_pilot(Parking, Membership, Zone, Camera, User, areas):
    cameras = Camera.objects.all()
    staff = User.objects.filter(user_type__in=["admin", "guest"])
    if not areas and not cameras.exists() and not staff.exists():
        return None

    parking = Parking.objects.create(
        name=PILOT_NAME,
        capacity=sum(len(entry["coordinates"]) for entry in areas),
    )
    cameras.update(parking=parking)
    for entry in areas:
        number = int(entry["area"])
        Zone.objects.create(
            parking=parking,
            number=number,
            spots=entry["coordinates"],
            camera=Camera.objects.filter(area=number).first(),
        )
    Membership.objects.bulk_create(
        [
            Membership(user=user, parking=parking, role="owner" if user.user_type == "admin" else "operator")
            for user in staff
        ]
    )
    return parking


def forwards(apps, schema_editor):
    build_pilot(
        apps.get_model("parking", "Parking"),
        apps.get_model("parking", "ParkingMembership"),
        apps.get_model("parking", "Zone"),
        apps.get_model("camera", "Camera"),
        apps.get_model("users", "User"),
        read_coordinates(),
    )


def backwards(apps, schema_editor):
    Parking = apps.get_model("parking", "Parking")
    Camera = apps.get_model("camera", "Camera")
    pilots = Parking.objects.filter(name=PILOT_NAME)
    Camera.objects.filter(parking__in=pilots).update(parking=None)
    pilots.delete()


class Migration(migrations.Migration):

    dependencies = [
        ("parking", "0001_initial"),
        ("camera", "0004_camera_parking_camera_stream_url"),
        ("users", "0002_user_language_user_phone_alter_user_user_type"),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
