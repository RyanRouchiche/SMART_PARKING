from venv import logger
import cv2
import json
import numpy as np
from django.shortcuts import render
from django.http import StreamingHttpResponse
import requests
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
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny



camera_paths = {
    1: r'C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\logic\Data\vid1.mp4',
    2: r'C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\logic\Data\vid1.mp4',
}


cameras = {floor: Camera(path, floor=floor) for floor, path in camera_paths.items()}
detector = Detector(camera_paths)



@api_view(['GET'])
@permission_classes([AllowAny])
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

        floor_str = str(floor)
        for spot_name, points in detector.spots_coordinates.get(floor_str, {}).items():
            source_points = np.float32(points)
            rect = detector.sort_parking_spot_points(source_points)
            w, h = detector.calculate_width_height(rect)
            dest_points = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
            m = cv2.getPerspectiveTransform(rect, dest_points)
            cropped_image = cv2.warpPerspective(frame, m, (w, h))

            output_dir = os.path.join(static_dir, 'cropped_spots', f'floor_{floor}')
            os.makedirs(output_dir, exist_ok=True)
            cropped_path = os.path.join(output_dir, f'{spot_name}.jpg')
            cv2.imwrite(cropped_path, cropped_image)

        camera.reset()

        images[floor] = f'/static/camera_snapshot_floor_{floor}.jpg'

    return render(request, 'pick_up_spot.html', {"images": images})


@api_view(['POST'])
@permission_classes([AllowAny])

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
@permission_classes([AllowAny])
def Video_Feed_api(request):
    # Check if the 'floor' parameter is provided
    floor = request.GET.get('floor')

    if not floor:
        # If no floor is specified, render the stream_feed.html template
        return render(request, 'stream_feed.html')

    try:
        # Convert the floor parameter to an integer
        floor = int(floor)

        # Validate the floor parameter
        if floor not in detector.camera_objects:
            return Response({'error': 'Invalid floor parameter'}, status=status.HTTP_400_BAD_REQUEST)

        # Function to generate video frames for the specified floor
        def generate_frames():
            frame_nmr = 0  # Frame counter
            cam = detector.camera_objects[floor]  # Get the camera for the floor

            while True:
                frame = cam.getFrame()  # Capture a frame from the camera
                if frame is None:
                    print(f"Error: Unable to capture a frame for floor {floor}")
                    continue

                floor_str = str(floor)

                if floor_str not in detector.spots_coordinates:
                    print(f"Error: Floor {floor_str} not found in spots_coordinates.")
                    continue

                available_spots = 0  # Counter for available spots

                # Iterate through each parking spot
                for spot_name, points in detector.spots_coordinates[floor_str].items():
                    # Convert the spot's coordinates to a numpy array
                    source_points = np.float32(points)

                    # Sort the points
                    rect = detector.sort_parking_spot_points(source_points)

                    # Define the destination points (cropped image size)
                    w, h = detector.calculate_width_height(rect)
                    dest_points = np.float32([
                        [0, 0],
                        [w, 0],
                        [w, h],
                        [0, h],
                    ])

                    # Compute the perspective transform matrix
                    m = cv2.getPerspectiveTransform(rect, dest_points)

                    # Apply the perspective warp
                    cropped_image = cv2.warpPerspective(frame, m, (w, h))
                    
                    

                    # Send the cropped image to the model API for classification
                    _, img_encoded = cv2.imencode('.jpg', cropped_image)
                    response = requests.post("http://127.0.0.1:8000/api/predict/", files={"file": img_encoded.tobytes()})

                    # Parse the model's response
                    if response.status_code == 200:
                        result = response.json().get("result", "unknown")
                    else:
                        result = "unknown"

                    # Update the detector.spots_status dictionary
                    detector.spots_status[floor_str][spot_name] = result

                    # Count available spots
                    if result == "empty":
                        available_spots += 1

                    # Determine the color based on the classification result
                    color = (0, 255, 0) if result == "empty" else (0, 0, 255)  # Green for empty, Red for occupied

                    # Draw the rectangle on the frame
                    pts = np.int32(rect)
                    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=1)

                    # Add the spot name and status
                    cv2.putText(frame, f"{spot_name}: {result}", (pts[0][0], pts[0][1] - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

                # Display the total number of available spots on the frame
                cv2.putText(frame, f"Available Spots: {available_spots}", (10, 30),
                            cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2, cv2.LINE_AA)

                # Encode the frame as JPEG
                _, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                # Yield the frame as part of the video stream
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

                frame_nmr += 1
                

        # Return the video stream as a response
        return StreamingHttpResponse(
            generate_frames(),
            content_type='multipart/x-mixed-replace; boundary=frame'
        )

    except ValueError:
        # Handle invalid floor parameter (e.g., non-integer values)
        return Response({'error': 'Invalid floor parameter'}, status=status.HTTP_400_BAD_REQUEST)





@api_view(['GET'])
@permission_classes([AllowAny])
def get_parking_data_api(request):
    # Ensure detector.camera_objects is initialized
    if not detector.camera_objects:
        return Response({'error': 'No camera objects found'}, status=status.HTTP_404_NOT_FOUND)

    # Get the available floors
    available_floors = list(detector.camera_objects.keys())

    # Initialize the available spots data
    available_spots_data = {}

    for floor in available_floors:
        floor_str = str(floor)  # Ensure consistent key format
        if floor_str not in detector.spots_status:
            available_spots_data[floor] = 0  # Default to 0 if no data is available
            continue

        # Count the number of available spots (empty spots)
        available_spots = sum(1 for spot_status in detector.spots_status[floor_str].values() if spot_status == "empty")
        available_spots_data[floor] = available_spots

    # Return the response with available floors and spots data
    return Response({
        'floors': available_floors,
        'available_spots_data': available_spots_data
    }, status=status.HTTP_200_OK)




