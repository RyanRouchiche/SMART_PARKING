import json
import os
import cv2
from django.conf import settings
import numpy as np
from .Camera import Camera

import random

class Detector:
    def __init__(self, cameras):
        #  creating  cam objects for each floor
        self.camera_objects = {floor: Camera(url, floor) for floor, url in cameras.items()}
        
        
        self.spots_coordinates = {} # stroing parking spot coordinates
        self.spots_status = {} # storing the parking spot statuses

        # creating a folder to save cropped parking spot images this step is optionnel
        self.output_dir = "cropped_spots"
        os.makedirs(self.output_dir, exist_ok=True) 

        # init parking spots 
        self.initialize_spots()
    
    # Simulated function to check if a parking spot is empty or occupied , we wait for ryan modele to give the exact classification the model will be implemented inside this function
    def empty_or_not(self):
        return random.choice([0, 1])  # Randomly returns 0 (occupied) or 1 (empty)



    def initialize_spots(self):
        # Path to the JSON file
        #json_file_path = os.path.join(settings.BASE_DIR, r"parking\logic\Spots\coordinates.json") 
        json_file_path = os.path.join(settings.BASE_DIR, "parking/Spots/coordinates.json")
        print(f"Loading coordinates from: {json_file_path}")

        # Load the JSON file
        if os.path.exists(json_file_path):
            with open(json_file_path, "r", encoding="utf-8") as file:
                data = json.load(file)
                print('data:', data)
        else:
            print("Error: JSON file with parking spot coordinates not found.")
            return

        # Parse the JSON data into the internal structure
        for floor_data in data:
            floor = int(floor_data["floor"])  # Get the floor number
            coordinates = floor_data["coordinates"]  # Get the coordinates dictionary

            # Use the dictionary structure directly for spots_coordinates
            self.spots_coordinates[floor] = coordinates

            # Initialize the status of each parking spot (randomly assigned for now)
            self.spots_status[floor] = {
                spot_name: self.empty_or_not() for spot_name in coordinates.keys()
            }
            print(f"Initialized spots for floor {floor}: {self.spots_coordinates[floor]}")
        print("Initialized spots_coordinates:", self.spots_coordinates)

    
    
    
    def markSpot(self, frame, floor, available_spots):
        # Iterate over each parking spot in the floor
        for spot_name, points in self.spots_coordinates[floor].items():
            pts = np.array(points, dtype=np.int32)  # Convert points to numpy array
            print('pts:',pts)

            # Create the area
            x_min, y_min = np.min(pts[:, 0]), np.min(pts[:, 1])
            x_max, y_max = np.max(pts[:, 0]), np.max(pts[:, 1])

            # Check if the coordinates are valid for the frame
            if x_min < 0 or y_min < 0 or x_max > frame.shape[1] or y_max > frame.shape[0]:
                print(f"Error: Invalid coordinates for {spot_name} on floor {floor}")
                continue

            # Crop the parking spot from the frame
            spot_crop = frame[y_min:y_max, x_min:x_max]

            # Check if the cropping is valid
            if spot_crop.size == 0:
                print(f"Error: Empty image for {spot_name} on floor {floor}")
                continue

            # Save cropped images (optional)
            save_path = os.path.join(self.output_dir, f"{floor}_{spot_name}.jpg")
            cv2.imwrite(save_path, spot_crop)

            # Get the parking spot status
            spot_status = self.spots_status[floor][spot_name]
            print('status',spot_status)
            color = (0, 255, 0) if spot_status else (0, 0, 255)  # Green if empty, red if occupied

            # Count available spots
            if spot_status:
                available_spots += 1

            # Draw the area of the parking space
            cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

            # Display the parking spot number in the center of the area
            center_x, center_y = (x_min + x_max) // 2, (y_min + y_max) // 2
            cv2.putText(frame, spot_name, (center_x, center_y),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

        return available_spots


    
    def displayStatusSpot(self, frame, available_spots):
        total_spots = sum(len(spots) for spots in self.spots_coordinates.values())  # Count all parking spots
        cv2.rectangle(frame, (50, 20), (400, 80), (0, 0, 0), -1)  # Draw a black box for text
        cv2.putText(frame, f"Available spots: {available_spots} / {total_spots}", 
                    (60, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1)
        

    # function to run the parking detection system
    def test_system(self):
        frame_nmr = 0  # Frame counter
        print("Type of detector.spots_coordinates:", type(detector.spots_coordinates))
        print("Value of detector.spots_coordinates:", detector.spots_coordinates)

        while True:
            for floor, cam in detector.camera_objects.items():
                frame = cam.getFrame()  # Get a frame from the video or camera
                if frame is None:
                    continue

                available_spots = 0  # Counter for available spots

                # Check if the floor exists in spots_coordinates
                if floor not in detector.spots_coordinates:
                    print(f"Error: Floor {floor} not found in spots_coordinates.")
                    continue

                # Refresh parking spot status every 20 frames to reduce CPU usage
                if frame_nmr % 20 == 0:
                    for spot_name, points in detector.spots_coordinates[floor].items():
                        detector.spots_status[floor][spot_name] = detector.empty_or_not()

                # Mark parking spots and count available spots
                available_spots = detector.markSpot(frame, floor, available_spots)

                # Display available spots on the frame
                detector.displayStatusSpot(frame, available_spots)

                # show the video frame with marked parking spots
                cv2.imshow(f"Floor {floor} - live detection", frame)

            frame_nmr += 1  

            # press 'q' to exit the system
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

  
        cv2.destroyAllWindows()
    
    def calculate_width_height(self , rect) : 
          # Calculate the width (distance between top-left and top-right, or bottom-left and bottom-right)
        width_top = np.linalg.norm(rect[0] - rect[1])  # Top-left to top-right
        width_bottom = np.linalg.norm(rect[2] - rect[3])  # Bottom-right to bottom-left
        width = max(int(width_top), int(width_bottom))

        # Calculate the height (distance between top-left and bottom-left, or top-right and bottom-right)
        height_left = np.linalg.norm(rect[0] - rect[3])  # Top-left to bottom-left
        height_right = np.linalg.norm(rect[1] - rect[2])  # Top-right to bottom-right
        height = max(int(height_left), int(height_right))

        return width, height
    
    def sort_parking_spot_points(self, pts):
        rect = np.zeros((4, 2), dtype="float32")
        # sum = x + y → top-left will have the smallest, bottom-right the largest
        s = pts.sum(axis=1)
        rect[0] = pts[np.argmin(s)]  # top-left
        rect[2] = pts[np.argmax(s)]  # bottom-right
        # diff = x - y → top-right will have the smallest, bottom-left the largest
        diff = np.diff(pts, axis=1)
        rect[1] = pts[np.argmin(diff)]  # top-right
        rect[3] = pts[np.argmax(diff)]  # bottom-left

        return rect
        

            

        
        
    

if __name__ == "__main__":
    cameras = {1: "Data/parking_crop_loop.mp4"}  
    detector = Detector(cameras)  
    detector.test_system()  
