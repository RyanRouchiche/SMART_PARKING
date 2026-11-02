import base64
import logging
import os

import cv2
import numpy as np
from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from camera.models import Camera
from camera.utils import calculate_width_height, sort_parking_spot_points, open_cameras, convert_ndarray_to_list
from .access import get_parking
from .models import Zone
from .serializers import AreaSerializer

logger = logging.getLogger(__name__)

CROPPED_SPOTS_DIR = os.path.join(settings.BASE_DIR, "cropped_spots")


@api_view(['GET'])
def snapshots(request):
    parking = get_parking(request, owner=True)
    images = {}
    for area, camera in open_cameras(parking.id).items():
        frame = camera.getFrame()
        if frame is None:
            logger.warning(f"Unable to capture a frame in area {area}")
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        images[area] = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
    return Response({'images': images})


@api_view(['GET', 'POST'])
def coordinates(request):
    if request.method == 'GET':
        parking = get_parking(request)
        return Response({'data': [{'area': str(z.number), 'coordinates': z.spots} for z in parking.zones.all()]})

    parking = get_parking(request, owner=True)
    serializer = AreaSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)

    validated_data = serializer.validated_data
    for area_data in validated_data:
        for spot, points in area_data['coordinates'].items():
            area_data['coordinates'][spot] = sort_parking_spot_points(np.array(points, dtype="float32"))

    with transaction.atomic():
        for area_data in validated_data:
            number = int(area_data['area'])
            Zone.objects.update_or_create(
                parking=parking,
                number=number,
                defaults={
                    'spots': convert_ndarray_to_list(area_data['coordinates']),
                    'camera': Camera.objects.filter(parking=parking, area=number).first(),
                },
            )

    cameras = open_cameras(parking.id)
    for area_data in validated_data:
        area = int(area_data["area"])
        camera = cameras.get(area)
        frame = camera.getFrame() if camera else None
        if frame is None:
            logger.warning(f"No frame available for area {area}")
            continue

        output_dir = os.path.join(CROPPED_SPOTS_DIR, str(parking.id), f'area_{area}')
        os.makedirs(output_dir, exist_ok=True)
        for spot_name, rect in area_data["coordinates"].items():
            w, h = calculate_width_height(rect)
            matrix = cv2.getPerspectiveTransform(rect, np.float32([[0, 0], [w, 0], [w, h], [0, h]]))
            cv2.imwrite(os.path.join(output_dir, f'{spot_name}.jpg'), cv2.warpPerspective(frame, matrix, (w, h)))

        camera.reset()

    return Response({'message': 'Coordinates saved'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def areas(request):
    parking = get_parking(request)
    return Response({'areas': list(parking.zones.values_list('number', flat=True))})
