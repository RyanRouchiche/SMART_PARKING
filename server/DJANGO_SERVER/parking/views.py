import base64
import json
import logging
import os

import cv2
import numpy as np
from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from camera.utils import calculate_width_height, sort_parking_spot_points, async_initialize_cameras, convert_ndarray_to_list
from users.permission import IsAdmin, IsAdminOrReadOnly
from .serializers import AreaSerializer

logger = logging.getLogger(__name__)

COORDINATES_FILE = os.path.join(settings.BASE_DIR, "parking", "Spots", "coordinates.json")
CROPPED_SPOTS_DIR = os.path.join(settings.BASE_DIR, "cropped_spots")


def read_coordinates():
    with open(COORDINATES_FILE, 'r', encoding='utf-8') as file:
        return json.load(file)


@api_view(['GET'])
@permission_classes([IsAdmin])
def snapshots(request):
    images = {}
    for area, camera in async_initialize_cameras().items():
        frame = camera.getFrame()
        if frame is None:
            logger.warning(f"Unable to capture a frame in area {area}")
            continue
        _, buffer = cv2.imencode('.jpg', frame)
        images[area] = f"data:image/jpeg;base64,{base64.b64encode(buffer).decode()}"
    return Response({'images': images})


@api_view(['GET', 'POST'])
@permission_classes([IsAdminOrReadOnly])
def coordinates(request):
    if request.method == 'GET':
        try:
            return Response({'data': read_coordinates()})
        except FileNotFoundError:
            return Response({'data': []})
        except json.JSONDecodeError:
            return Response({'error': 'coordinates.json is malformed'}, status=500)

    serializer = AreaSerializer(data=request.data, many=True)
    serializer.is_valid(raise_exception=True)

    validated_data = serializer.validated_data
    for area_data in validated_data:
        for spot, points in area_data['coordinates'].items():
            area_data['coordinates'][spot] = sort_parking_spot_points(np.array(points, dtype="float32"))

    with open(COORDINATES_FILE, "w", encoding="utf-8") as file:
        json.dump(convert_ndarray_to_list(validated_data), file, indent=4, ensure_ascii=False)

    cameras = async_initialize_cameras()
    for area_data in validated_data:
        area = area_data["area"]
        camera = cameras.get(int(area))
        frame = camera.getFrame() if camera else None
        if frame is None:
            logger.warning(f"No frame available for area {area}")
            continue

        output_dir = os.path.join(CROPPED_SPOTS_DIR, f'area_{area}')
        os.makedirs(output_dir, exist_ok=True)
        for spot_name, rect in area_data["coordinates"].items():
            w, h = calculate_width_height(rect)
            matrix = cv2.getPerspectiveTransform(rect, np.float32([[0, 0], [w, 0], [w, h], [0, h]]))
            cv2.imwrite(os.path.join(output_dir, f'{spot_name}.jpg'), cv2.warpPerspective(frame, matrix, (w, h)))

        camera.reset()

    return Response({'message': 'Coordinates saved'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([AllowAny])
def areas(request):
    try:
        data = read_coordinates()
    except (FileNotFoundError, json.JSONDecodeError):
        data = []
    return Response({'areas': sorted(int(entry["area"]) for entry in data if "area" in entry)})
