import os

import cv2
from django.conf import settings
from django.db import transaction

from camera.models import Camera
from camera.services import current_frames
from detection.geometry import crop_spot, order_corners
from .models import Zone

CROPPED_SPOTS_DIR = os.path.join(settings.BASE_DIR, "cropped_spots")


def zone_layouts(parking):
    return [{'area': str(z.number), 'coordinates': z.spots} for z in parking.zones.all()]


def zone_numbers(parking):
    return list(parking.zones.values_list('number', flat=True))


def save_zones(parking, areas):
    layouts = {
        int(a['area']): {name: order_corners(points) for name, points in a['coordinates'].items()}
        for a in areas
    }
    with transaction.atomic():
        for number, spots in layouts.items():
            Zone.objects.update_or_create(
                parking=parking,
                number=number,
                defaults={
                    'spots': {name: rect.tolist() for name, rect in spots.items()},
                    'camera': Camera.objects.filter(parking=parking, area=number).first(),
                },
            )
    export_spot_crops(parking, layouts)


def export_spot_crops(parking, layouts):
    frames = current_frames(parking.id, set(layouts))
    for number, spots in layouts.items():
        frame = frames.get(number)
        if frame is None:
            continue
        output_dir = os.path.join(CROPPED_SPOTS_DIR, str(parking.id), f'area_{number}')
        os.makedirs(output_dir, exist_ok=True)
        for name, rect in spots.items():
            cv2.imwrite(os.path.join(output_dir, f'{name}.jpg'), crop_spot(frame, rect))
