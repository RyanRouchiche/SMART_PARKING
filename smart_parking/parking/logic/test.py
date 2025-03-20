# import cv2
# import json
# import numpy as np
# from Draw import Draw
# from Camera import Camera
# from Detector import Detector
# import os

# def test_system():
#     # set  cameras with their video file paths
#     cameras = {
#         1: "Data/parking_crop_loop.mp4",
#     }

#     # creating Camera objects for each floor
#     camera_objects = {floor: Camera(url, floor) for floor, url in cameras.items()}
#     spots_coordinates = {}  # stroing parking spot coordinates

#     # processeing each floor's camera
#     for floor, cam in camera_objects.items():
#         frame = cam.getFrame()  # get the first frame from the video
#         if frame is None:
#             print(f"Error: Unable to retrieve a frame for floor {floor}")
#             continue

#         draw = Draw(floor, frame)  # creating a Draw object

#         # loading parking spot coordinates from JSON file if available
#         if draw.coordinates:
#             spots_coordinates[floor] = draw.coordinates
#         else:
#             print(f"Select parking spots for floor {floor} (Press 'q' to confirm)")
#             draw.get_points()  # Allow user to select parking spots
#             spots_coordinates[floor] = draw.coordinates

#         # # generating and save the mask
#         # mask = draw.drawMask()
#         # draw.saveMask(mask)
#         # masks[floor] = mask
        
        
#         output_dir = "cropped_spots"
#         os.makedirs(output_dir, exist_ok=True)

#     # starting video playback and show detected parking spots in real time
#     while True:
#         for floor, cam in camera_objects.items():
#             frame = cam.getFrame()  # Get the current frame from the video
#             if frame is None:
#                 continue

#             # draw parking spots using coordinates from the json file
#             if floor in spots_coordinates:
#                 for spot in spots_coordinates[floor]:
                    
#                     for spot_name, points in spot.items():
#                         pts = np.array(points, dtype=np.int32)
                        
#                         #  get the area of spots (rectangle)
#                         x_min = np.min(pts[:, 0])  # Min des X
#                         y_min = np.min(pts[:, 1])  # Min des Y
#                         x_max = np.max(pts[:, 0])  # Max des X
#                         y_max = np.max(pts[:, 1])  # Max des Y

#                         # check indices
#                         if x_min < 0 or y_min < 0 or x_max > frame.shape[1] or y_max > frame.shape[0]:
#                             print(f"Erreur : coordinates doesnt exists {spot_name} at floor {floor}")
#                             continue

#                         # crop each spot
#                         spot_crop = frame[y_min:y_max, x_min:x_max]  

#                         # check if the area  is a valid area a true rectangle
#                         if spot_crop.size == 0:
#                             print(f"Erreur : None Image {spot_name} in floor {floor}")
#                             continue

#                         # save spot cropped  an optionnel step we can remove it its just for checking
#                         save_path = os.path.join(output_dir, f"{floor}_{spot_name}.jpg")
#                         cv2.imwrite(save_path, spot_crop)
#                         print(f"Spot {spot_name} floor {floor} saved in {save_path}")


#                         # drawing a blue polygon for the parking spot
#                         cv2.polylines(frame, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

#                         # displaying the spot name on the video in inside the box
#                         center_x = (x_min + x_max) // 2
#                         center_y = (y_min + y_max) // 2
#                         cv2.putText(frame, spot_name, (center_x, center_y),
#                                     cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

#             # show the processed video with parking spots marked
#             cv2.imshow(f"Floor {floor} - Live Detection", frame)

#         # Press 'q' to exit the detection
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break

#     # Close all OpenCV windows
#     cv2.destroyAllWindows()

# if __name__ == "__main__":
#     test_system()
import cv2
import json
import numpy as np
import os
import random 
from Draw import Draw
from Camera import Camera
from Detector import Detector

# simulat function for checking if a parking spot is empty or occupied inside it will  be the modele that classify the images and return wether 0  or 1
def empty_or_not():
    return random.choice([0, 1])  # Randomly return 0 (occupied) or 1 (empty)

def test_system():
    # set cameras with their video paths
    cameras = {
        1: "Data/parking_crop_loop.mp4",
    }

    # creating  cam objects for each floor
    camera_objects = {floor: Camera(url, floor) for floor, url in cameras.items()}
    spots_coordinates = {}  # stroing parking spot coordinates
    spots_status = {}  # storing the parking spot statuses

    # creating a folder to save cropped parking spot images this step is optionnel
    output_dir = "cropped_spots"
    os.makedirs(output_dir, exist_ok=True)

    # loading parking spot coordinates from JSON file
    for floor, cam in camera_objects.items():
        frame = cam.getFrame()  # get the first frame from the video
        if frame is None:
            print(f"Error: Unable to retrieve a frame for floor {floor}")
            continue

        draw = Draw(floor, frame)  # iinstance a draw objet 

        if draw.coordinates:
            spots_coordinates[floor] = draw.coordinates  #  load save coordinates
            spots_status[floor] = {spot_name: empty_or_not() for spot in draw.coordinates for spot_name in spot}
        else:
            print(f"Select parking spots for floor {floor} (Press 'q' to confirm)")
            draw.get_points()  
            spots_coordinates[floor] = draw.coordinates  # save new coordinates
            spots_status[floor] = {spot_name: empty_or_not() for spot in draw.coordinates for spot_name in spot}

    frame_nmr = 0  # counter we re going to re do the op each 50 frames to give the processor time to relax

    while True:
        for floor, cam in camera_objects.items():
            frame = cam.getFrame()  # get a shot from the cam or the video for simulation
            if frame is None:
                continue

            available_spots = 0  # count availb spot

            # refresh each 50 frames
            if frame_nmr % 50 == 0:
                for spot in spots_coordinates[floor]:
                    for spot_name in spot.keys():
                        spots_status[floor][spot_name] = empty_or_not()  # change status every 50 frames

            # Draw parking spots
            for spot in spots_coordinates[floor]:
                for spot_name, points in spot.items():
                    pts = np.array(points, dtype=np.int32)  # convert points to np array

                    # to identify the area arround the parking spots a shape lik e a rectangle
                    x_min = np.min(pts[:, 0])
                    y_min = np.min(pts[:, 1])
                    x_max = np.max(pts[:, 0])
                    y_max = np.max(pts[:, 1])

                    # check if the coordinates are valide dont exceed the pixels of the frame
                    if x_min < 0 or y_min < 0 or x_max > frame.shape[1] or y_max > frame.shape[0]:
                        print(f"Error: invaliod coordinates for {spot_name} on floor {floor}")
                        continue

                    # crop spot in the frames these spots are going to be fed to the model
                    spot_crop = frame[y_min:y_max, x_min:x_max]

                    # chekc if the cropping is valid
                    if spot_crop.size == 0:
                        print(f"Error: Empty image for {spot_name} on floor {floor}")
                        continue

                    # Save the cropped parking spot frame this tezp is also optionnel just to see the cropping images are good or not
                    save_path = os.path.join(output_dir, f"{floor}_{spot_name}.jpg")
                    cv2.imwrite(save_path, spot_crop)

                    # decide the spot status (0 = occupied, 1 = empty)
                    spot_status = spots_status[floor][spot_name]
                    color = (0, 255, 0) if spot_status else (0, 0, 255)  # Green if empty, Red if occupied
                    if spot_status:
                        available_spots += 1  # Count empty spots

                    # draw a shape like rectangle arround the spot
                    cv2.polylines(frame, [pts], isClosed=True, color=color, thickness=2)

                    # display the spot name in center of the box
                    center_x = (x_min + x_max) // 2
                    center_y = (y_min + y_max) // 2
                    cv2.putText(frame, spot_name, (center_x, center_y),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)

            # show a text inside the frame tells the number of empty spots
            total_spots = sum(len(spots) for spots in spots_coordinates.values())  # total number spots
            cv2.rectangle(frame, (50, 20), (400, 80), (0, 0, 0), -1)  # a decoration to draw a balck box
            cv2.putText(frame, f"Available spots: {available_spots} / {total_spots}", 
                        (60,60), cv2.FONT_HERSHEY_SIMPLEX, 0.75, (255, 255, 255), 1)

            # show video with the spots marked
            cv2.imshow(f"Floor {floor} - live detection", frame)

        frame_nmr += 1  # ++

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # close opencv windows
    cv2.destroyAllWindows()

if __name__ == "__main__":
    test_system()
