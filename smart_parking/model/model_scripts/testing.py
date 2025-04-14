import cv2
import numpy as np
import json
import os
from datetime import datetime

# Load the image
with open("image_path.txt", "r") as f:
    image_name = f.read().strip()
image_path = r"F:\downloads\pklot\train\images"
image_path = os.path.join(image_path, image_name)
image_path = image_path + ".jpg"
image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Image not found at {image_path}")

# Path to the coordinates.json file
coordinates_file = r"F:\Github\SMART_PARKING\smart_parking\model\model_scripts\points.json"

# Path to save cropped spots
output_folder = r"F:\Github\SMART_PARKING\smart_parking\model\model_images"

i = 0

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
    # print(f"Processing floor {floor} with coordinates: {coordinates}")

    for spot_name, spot_points in coordinates.items():
        # Convert the spot's coordinates to a numpy array
        source_points = np.float32(spot_points['points'])
        print(source_points)

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
        
        # # Check if the spot is occupied or not
        if spot_points['occupied'] == 1:
            label_folder = os.path.join(output_folder, "1")
        else:
            label_folder = os.path.join(output_folder, "0")

        os.makedirs(label_folder, exist_ok=True)  # Make sure the folder exists

        # Use timestamp for filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        output_path = os.path.join(label_folder, f"{timestamp}.jpg")
        cv2.imwrite(output_path, cropped_image)
        
        # Print the saved image path
        print(f"Saved cropped spot {spot_name} on floor {floor} to {output_path}")
        spot2 = data[0]["coordinates"].get("Spot 2")
        i += 1

print("All spots have been processed and saved.")