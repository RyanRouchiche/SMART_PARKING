# import cv2
# import numpy as np
# import json

# image = cv2.imread(r"C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\static\camera_snapshot_floor_1.jpg")


# source_points = np.float32([
#                 [
#                     288,
#                     426
#                 ],
#                 [
#                     285,
#                     386
#                 ],
#                 [
#                     365,
#                     427
#                 ],
#                 [
#                     362,
#                     378
#                 ]
            
# ])

# def sort_parking_spot_points(pts):
#     """
#     Takes 4 points and returns them in the order:
#     [top-left, top-right, bottom-right, bottom-left]

#     pts: numpy array of shape (4, 2)
#     """
#     rect = np.zeros((4, 2), dtype="float32")

#     # sum = x + y → top-left will have the smallest, bottom-right the largest
#     s = pts.sum(axis=1)
#     rect[0] = pts[np.argmin(s)]  # top-left
#     rect[2] = pts[np.argmax(s)]  # bottom-right

#     # diff = x - y → top-right will have the smallest, bottom-left the largest
#     diff = np.diff(pts, axis=1)
#     rect[1] = pts[np.argmin(diff)]  # top-right
#     rect[3] = pts[np.argmax(diff)]  # bottom-left

#     return rect


# points = sort_parking_spot_points(source_points)

# w , h  = 200 , 100
# dest_points  = np.float32([
#     [0,0],
#     [w,0],
#     [w,h],
#     [0,h],
    
# ])


# m = cv2.getPerspectiveTransform(points , dest_points)
# f = cv2.warpPerspective(image , m , (w , h))
# cv2.imshow('frame' , f)


# cv2.waitKey(0)

import cv2
import numpy as np
import json
import os

# Load the image
image = cv2.imread(r"C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\static\camera_snapshot_floor_1.jpg")

# Path to the coordinates.json file
coordinates_file = r"C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\parking\logic\Spots\coordinates.json"

# Path to save cropped spots
output_folder = r"C:\Users\redah\OneDrive\Desktop\smart_parking_project\smart_parking\cropped_spots"

# Ensure the output folder exists
os.makedirs(output_folder, exist_ok=True)

def sort_parking_spot_points(pts):
    """
    Takes 4 points and returns them in the order:
    [top-left, top-right, bottom-right, bottom-left]
    """
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

def calculate_width_height(rect):

    # Calculate the width (distance between top-left and top-right, or bottom-left and bottom-right)
    width_top = np.linalg.norm(rect[0] - rect[1])  # Top-left to top-right
    width_bottom = np.linalg.norm(rect[2] - rect[3])  # Bottom-right to bottom-left
    width = max(int(width_top), int(width_bottom))

    # Calculate the height (distance between top-left and bottom-left, or top-right and bottom-right)
    height_left = np.linalg.norm(rect[0] - rect[3])  # Top-left to bottom-left
    height_right = np.linalg.norm(rect[1] - rect[2])  # Top-right to bottom-right
    height = max(int(height_left), int(height_right))

    return width, height

# Load coordinates from the JSON file
with open(coordinates_file, 'r') as file:
    data = json.load(file)

# Iterate through each floor and its parking spots
for floor_data in data:
    floor = floor_data["floor"]
    coordinates = floor_data["coordinates"]

    for spot_name, spot_points in coordinates.items():
        # Convert the spot's coordinates to a numpy array
        source_points = np.float32(spot_points)

        # Sort the points
        points = sort_parking_spot_points(source_points)

        # Calculate the width and height dynamically
        w, h = calculate_width_height(points)

        # Define the destination points (cropped image size)
        dest_points = np.float32([
            [0, 0],
            [w, 0],
            [w, h],
            [0, h],
        ])

        # Compute the perspective transform matrix
        m = cv2.getPerspectiveTransform(points, dest_points)

        # Apply the perspective warp
        cropped_image = cv2.warpPerspective(image, m, (w, h))

        # Save the cropped image to the output folder
        output_path = os.path.join(output_folder, f"{floor}_{spot_name}.jpg")
        cv2.imwrite(output_path, cropped_image)

        print(f"Saved cropped spot {spot_name} on floor {floor} to {output_path}")

print("All spots have been processed and saved.")