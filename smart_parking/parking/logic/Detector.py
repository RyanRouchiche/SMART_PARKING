import os
import cv2
import numpy as np
from Camera import Camera
from Draw import Draw
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
        # loading parking spot coordinates from JSON file
        for floor, cam in self.camera_objects.items():
            frame = cam.getFrame()  # Get the first frame from the camera
            if frame is None:
                print(f"Error: Unable to retrieve a frame for floor {floor}")
                continue

            draw = Draw(floor, frame)  # iinstance a draw objet 
            
            # If coordinates already exist, use them
            if draw.coordinates:
                self.spots_coordinates[floor] = draw.coordinates #  load save coordinates
            else:
                # If no coordinates, select them
                print(f"Select parking spots for floor {floor} (Press 'q' to confirm)")
                draw.get_points()
                self.spots_coordinates[floor] = draw.coordinates # save new coordinates

            # Initialize the status of each parking spot (randomly assigned)
            self.spots_status[floor] = {spot_name: self.empty_or_not() for spot in draw.coordinates for spot_name in spot}

    # Function to mark parking spots on the video frame
    def markSpot(self, frame, floor, available_spots):
        for spot in self.spots_coordinates[floor]:
            for spot_name, points in spot.items():
                pts = np.array(points, dtype=np.int32)  # converting points to np array

                # create the area
                x_min, y_min = np.min(pts[:, 0]), np.min(pts[:, 1])
                x_max, y_max = np.max(pts[:, 0]), np.max(pts[:, 1])

                # check if the coordinates are valid for the frame
                if x_min < 0 or y_min < 0 or x_max > frame.shape[1] or y_max > frame.shape[0]:
                    print(f"Error: Invalid coordinates for {spot_name} on floor {floor}")
                    continue

                # crop the parking spot from the frame
                spot_crop = frame[y_min:y_max, x_min:x_max]

                # check if the cropping is valid
                if spot_crop.size == 0:
                    print(f"Error: Empty image for {spot_name} on floor {floor}")
                    continue

                # save cropped images optionnel we could remove it just also to check
                save_path = os.path.join(self.output_dir, f"{floor}_{spot_name}.jpg")
                cv2.imwrite(save_path, spot_crop)

                # get the parking spot status 
                spot_status = self.spots_status[floor][spot_name]
                color = (0, 255, 0) if spot_status else (0, 0, 255)  # Green if empty, red if occupied
                
                # count available spots
                if spot_status:
                    available_spots += 1

                # draw the area of the parking space
                cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

                # display the parking sot number in center of thz area
                center_x, center_y = (x_min + x_max) // 2, (y_min + y_max) // 2
                cv2.putText(frame, spot_name, (center_x, center_y),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        return available_spots  

    # function to display the total number of available spots
    def displayStatusSpot(self, frame, available_spots):
        total_spots = sum(len(spots) for spots in self.spots_coordinates.values())  # Count all parking spots
        cv2.rectangle(frame, (50, 20), (400, 80), (0, 0, 0), -1)  # Draw a black box for text
        cv2.putText(frame, f"Available spots: {available_spots} / {total_spots}", 
                    (60, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1)

    # function to run the parking detection system
    def test_system(self):
        frame_nmr = 0  
        while True:
            for floor, cam in self.camera_objects.items():
                frame = cam.getFrame()  # get a shot from the viodeo or the cameras
                if frame is None:
                    continue

                available_spots = 0  

                # resfresh parking spot status every 50 frames let cpu chill
                if frame_nmr % 50 == 0:
                    for spot in self.spots_coordinates[floor]:
                        for spot_name in spot.keys():
                            self.spots_status[floor][spot_name] = self.empty_or_not()

                # mark parking spots and count available 
                available_spots = self.markSpot(frame, floor, available_spots)

                # display available spots on the frame
                self.displayStatusSpot(frame, available_spots)

                # show the video frame with marked parking spots
                cv2.imshow(f"Floor {floor} - live detection", frame)

            frame_nmr += 1  

            # press 'q' to exit the system
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

  
        cv2.destroyAllWindows()


if __name__ == "__main__":
    cameras = {1: "Data/parking_crop_loop.mp4"}  
    detector = Detector(cameras)  
    detector.test_system()  
