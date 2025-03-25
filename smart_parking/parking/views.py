import cv2
import json
import numpy as np
from django.shortcuts import render
from django.http import StreamingHttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .logic.serializers import SpotSerializer
from .logic.Detector import Detector
from .logic.Camera import Camera
from .logic.Draw import Draw
from django.conf import settings
import os
from .logic.serializers import FloorSerializer



camera_paths = {
    1: r'C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\logic\Data\parking_crop_loop.mp4',
}


cameras = {floor: Camera(path, floor=floor) for floor, path in camera_paths.items()}
detector = Detector(camera_paths)



@api_view(['GET'])
def pick_up_spot_api(request):
    images = {}
    static_dir = settings.STATICFILES_DIRS[0]

    if not os.path.exists(static_dir):
        os.makedirs(static_dir)

    for floor, camera in cameras.items():
        frame = camera.getFrame()
        if frame is None:
            print(f"Unable to capture a frame for floor {floor}")
            continue

        img_path = os.path.join(static_dir, f'camera_snapshot_floor_{floor}.jpg')
        cv2.imwrite(img_path, frame)

        # Reset the camera to the beginning of the video
        camera.reset()

        images[floor] = f'/static/camera_snapshot_floor_{floor}.jpg'

    return render(request, 'pick_up_spot.html', {"images": images})


@api_view(['POST'])
def save_spot_coordinates_api(request):
    print("ncoming data:", request.data)  
    serializer = FloorSerializer(data=request.data, many=True)
    if serializer.is_valid():
        validated_data = serializer.validated_data
        print("Validated data:", validated_data)  

        #  the path to the JSON file inside the logic/Spots folder of the parking app
        json_file_path = os.path.join(
            settings.BASE_DIR, "parking/logic/Spots/coordinates.json"
        )

        #  directory exists
        directory = os.path.dirname(json_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)

        #  existing data from the JSON file
        if os.path.exists(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as file:
                try:
                    data = json.load(file)
                except json.JSONDecodeError:
                    data = []
        else:
            data = []

        #  new data to the existing data
        data.extend(validated_data)

        #  updated data back to the JSON file
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

        return Response({"message": "Spots saved successfully"}, status=status.HTTP_201_CREATED)

    print("Errors:", serializer.errors)  
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def Video_Feed_api(request) : 

    
    def generate_frames():
        frame_nmr = 0  #
        while True:
            for floor, cam in detector.camera_objects.items():
                frame = cam.getFrame()  #  frame from the video or camera
                if frame is None:
                    print(f"Error: Unable to capture a frame from the camera on floor {floor}")
                    continue

                available_spots = 0 

                floor_str = str(floor)

        
                print("spots_coordinates:", detector.spots_coordinates)
                print("floor:", floor_str)

                if floor_str not in detector.spots_coordinates:
                    print(f"Error: Floor {floor_str} not found in spots_coordinates.")
                    continue

                if frame_nmr % 50 == 0:
                    for spot_name, points in detector.spots_coordinates[floor_str].items():
                        detector.spots_status[floor_str][spot_name] = detector.empty_or_not()

                #  parking spots and count available spots
                available_spots = detector.markSpot(frame, floor_str, available_spots)

                #  available spots on the frame
                detector.displayStatusSpot(frame, available_spots)

                #  the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Yield the frame as part of the video stream
                yield (b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            frame_nmr += 1
      
    return StreamingHttpResponse(
        generate_frames(),
        content_type='multipart/x-mixed-replace; boundary=frame'
    )