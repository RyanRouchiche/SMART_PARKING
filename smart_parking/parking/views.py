from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny , IsAuthenticated 
from rest_framework import status
import os
import cv2
import numpy as np
from django.conf import settings
from camera.utils import calculate_width_height , sort_parking_spot_points , async_initialize_cameras , convert_ndarray_to_list
from .serializers import AreaSerializer
import json
from django.http import JsonResponse
from users.permission import IsAdmin
from rest_framework.views import APIView
import logging
logger = logging.getLogger(__name__)

@api_view(['GET'])
@permission_classes([IsAuthenticated , IsAdmin  ])
def pick_up_spot_api(request):

    images = {}
    static_dir = os.path.join(settings.BASE_DIR, 'staticfiles')

    cameras = async_initialize_cameras()

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    for area, camera in cameras.items():
        frame = camera.getFrame()
        if frame is None:
            print(f"Unable to capture a frame in area {area}")
            continue

        img_path = os.path.join(static_dir, f'camera_snapshot_area_{area}.jpg')
        print(f"Saving image to: {img_path}")
        cv2.imwrite(img_path, frame)
 
        images[area] = f'{settings.STATIC_URL}camera_snapshot_area_{area}.jpg'
        print(f"Image URL: {settings.STATIC_URL}camera_snapshot_area_{area}.jpg")

    return render(request, 'pick_up_spot.html', {"images": images})




@api_view(['POST'])
@permission_classes([IsAuthenticated , IsAdmin])

def save_spot_coordinates_api(request):
    print("Incoming data:", request.data)
    serializer = AreaSerializer(data=request.data, many=True)

    # Initialize cameras synchronously
    cameras = async_initialize_cameras()

    if serializer.is_valid():
        validated_data = serializer.validated_data

        for area_data in validated_data:
            for spot, points in area_data['coordinates'].items():
                sorted_pts = sort_parking_spot_points(np.array(points, dtype="float32"))
                area_data['coordinates'][spot] = sorted_pts

        json_file_path = os.path.join(settings.BASE_DIR, "parking", "Spots", "coordinates.json")

        # Delete the old JSON file
        if os.path.exists(json_file_path):
            try:
                os.remove(json_file_path)
            except Exception as e:
                return Response({"error": f"Error deleting JSON file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Convert data to a serializable format
            serializable_data = convert_ndarray_to_list(validated_data)
            with open(json_file_path, "w", encoding="utf-8") as file:
                json.dump(serializable_data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            return Response({"error": f"Error writing to JSON file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Save cropped images
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        for area_data in validated_data:
            area = area_data["area"]
            coordinates = area_data["coordinates"]

            camera = cameras.get(int(area))
            if camera is None:
                print(f"[Warning] No camera found in area {area}")
                continue

            frame = camera.getFrame()
            if frame is None:
                print(f"[Error] Unable to capture an image in area {area}")
                continue

            for spot_name, sorted_pts in coordinates.items():
                try:
                    rect = np.array(sorted_pts, dtype="float32")
                    w, h = calculate_width_height(rect)
                    dest_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
                    matrix = cv2.getPerspectiveTransform(rect, dest_pts)
                    cropped = cv2.warpPerspective(frame, matrix, (w, h))

                    output_dir = os.path.join(static_dir, 'cropped_spots', f'area_{area}')
                    os.makedirs(output_dir, exist_ok=True)
                    out_path = os.path.join(output_dir, f'{spot_name}.jpg')
                    cv2.imwrite(out_path, cropped)
                except Exception as e:
                    print(f"[Error] Cropping spot {spot_name} in area {area}: {str(e)}")

            camera.reset()

        return Response({"message": "Coordinates sorted, saved, and cropped images generated."}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@permission_classes([IsAuthenticated ])
def get_available_areas(request):
    try:
        coordinates_file = os.path.join(settings.BASE_DIR, "parking/Spots/coordinates.json")
        with open(coordinates_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        areas = [int(area_entry["area"]) for area_entry in data if "area" in area_entry]
        return JsonResponse(sorted(areas), safe=False)
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Failed to load coordinates file: {e}'}, status=500)


@api_view(["GET"])
@permission_classes([AllowAny])
def get_jsonFile(request):
    coordinates_file = os.path.join(settings.BASE_DIR, "parking", "Spots", "coordinates.json")

    if not os.path.exists(coordinates_file):
        return Response({'error': 'Le fichier coordinates.json est introuvable.'}, status=404)

    try:
        with open(coordinates_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            logger.info("Contenu du fichier coordinates.json chargé avec succès.")
            return Response({"data": data}, status=200)

    except json.JSONDecodeError as e:
        logger.error(f"Erreur de décodage JSON : {e}")
        return Response({'error': 'Erreur de format JSON dans coordinates.json.'}, status=400)

    except Exception as e:
        logger.exception("Une erreur inattendue est survenue.")
        return Response({'error': f'Erreur inattendue : {str(e)}'}, status=500)


class stream_page(APIView) : 
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) : 
        return render(request, 'video_feed.html')

