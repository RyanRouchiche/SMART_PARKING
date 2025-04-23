from django.shortcuts import render
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework import status
import os
import cv2
import numpy as np
from django.conf import settings
from .Camera import Camera
from .Detector import Detector
from .serializers import FloorSerializer
import json
from django.http import JsonResponse



camera_paths = {
    1: os.path.join(settings.BASE_DIR, 'parking', 'Data', 'parking_crop_loop.mp4'),
}


cameras = {floor: Camera(path, floor=floor) for floor, path in camera_paths.items()}
detector = Detector(camera_paths)



@api_view(['GET'])
@permission_classes([AllowAny])
def pick_up_spot_api(request):
    images = {}
    static_dir = os.path.join(settings.BASE_DIR, 'static')  
    

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    for floor, camera in cameras.items():
        frame = camera.getFrame()
        if frame is None:
            print(f"Unable to capture a frame for floor {floor}")
            continue

        img_path = os.path.join(static_dir, f'camera_snapshot_floor_{floor}.jpg')
        print(f"Saving image to: {img_path}")
        cv2.imwrite(img_path, frame)

        images[floor] = f'{settings.STATIC_URL}camera_snapshot_floor_{floor}.jpg'
        
        print(f"Image URL: {settings.STATIC_URL}camera_snapshot_floor_{floor}.jpg")

    return render(request, 'pick_up_spot.html', {"images": images})


def convert_ndarray_to_list(data):
    if isinstance(data, dict):
        return {k: convert_ndarray_to_list(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_ndarray_to_list(i) for i in data]
    elif isinstance(data, np.ndarray):
        return data.tolist()
    return data

@api_view(['POST'])
@permission_classes([AllowAny])
def save_spot_coordinates_api(request):
    print("Incoming data:", request.data)
    serializer = FloorSerializer(data=request.data, many=True)
    
    if serializer.is_valid():
        validated_data = serializer.validated_data

        for floor_data in validated_data:
            for spot, points in floor_data['coordinates'].items():
                sorted_pts = detector.sort_parking_spot_points(np.array(points, dtype="float32"))
                floor_data['coordinates'][spot] = sorted_pts

        json_file_path = os.path.join(settings.BASE_DIR, "parking", "Spots", "coordinates.json")
        
        # Supprimer l'ancien fichier
        if os.path.exists(json_file_path):
            try:
                os.remove(json_file_path)
            except Exception as e:
                return Response({"error": f"Erreur suppression fichier JSON : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            # Convertir les données avant JSON
            serializable_data = convert_ndarray_to_list(validated_data)
            with open(json_file_path, "w", encoding="utf-8") as file:
                json.dump(serializable_data, file, indent=4, ensure_ascii=False)
        except Exception as e:
            return Response({"error": f"Erreur lors de l'écriture JSON : {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Sauvegarde des images croppées
        static_dir = os.path.join(settings.BASE_DIR, 'static')
        for floor_data in validated_data:
            floor = floor_data["floor"]
            coordinates = floor_data["coordinates"]

            camera = cameras.get(int(floor))
            if camera is None:
                print(f"[Avertissement] Aucune caméra trouvée pour l'étage {floor}")
                continue

            frame = camera.getFrame()
            if frame is None:
                print(f"[Erreur] Impossible de capturer une image pour l'étage {floor}")
                continue

            for spot_name, sorted_pts in coordinates.items():
                try:
                    rect = np.array(sorted_pts, dtype="float32")
                    w, h = detector.calculate_width_height(rect)
                    dest_pts = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
                    matrix = cv2.getPerspectiveTransform(rect, dest_pts)
                    cropped = cv2.warpPerspective(frame, matrix, (w, h))

                    output_dir = os.path.join(static_dir, 'cropped_spots', f'floor_{floor}')
                    os.makedirs(output_dir, exist_ok=True)
                    out_path = os.path.join(output_dir, f'{spot_name}.jpg')
                    cv2.imwrite(out_path, cropped)
                except Exception as e:
                    print(f"[Erreur] Cropping spot {spot_name} sur étage {floor} : {str(e)}")

            camera.reset()

        return Response({"message": "Coordonnées triées, JSON sauvegardé, images croppées générées."}, status=status.HTTP_201_CREATED)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@permission_classes([AllowAny])
def get_available_floors(request):
    try:
        coordinates_file = os.path.join(settings.BASE_DIR, "parking/Spots/coordinates.json")
        with open(coordinates_file, 'r', encoding='utf-8') as file:
            data = json.load(file)

        floors = [int(floor_entry["floor"]) for floor_entry in data if "floor" in floor_entry]
        return JsonResponse(sorted(floors), safe=False)
    
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Failed to load coordinates file: {e}'}, status=500)

@permission_classes([AllowAny])
def stream_page(request):
    return render(request, 'video_feed.html')