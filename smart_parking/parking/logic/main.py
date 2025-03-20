import cv2
import numpy as np
import json

from pathlib import Path

base_dir = Path(__file__).resolve().parents[1] 
print('base directory : ' ,  base_dir)


image_path = base_dir /"logic"/ "Data" / "spotpng.png"
mask_path = base_dir / "logic" / "Mask" / "mask.png"
json_path = base_dir / "logic" / "Spots" / "coordinates.json"


print("Image Path:", image_path)
print("Mask Path:", mask_path)
print("JSON Path:", json_path)


if not image_path.exists():
    print(f"Error: Image file not found at {image_path}")
    exit()
if not mask_path.exists():
    print(f"Error: Mask file not found at {mask_path}")
    exit()
if not json_path.exists():
    print(f"Error: JSON file not found at {json_path}")
    exit()

# Load the original image
frame = cv2.imread(image_path)

# Load the mask in grayscale
mask = cv2.imread(mask_path, 0)

# checking if images are loaded correctly
if frame is None or mask is None:
    print("Error: Unable to load the image or mask.")
    exit()

# resizing mask if needed
if mask.shape != frame.shape[:2]:  
    print("Resizing mask to match image size...")
    mask = cv2.resize(mask, (frame.shape[1], frame.shape[0]))

#  loading parking spot coordinates ---
with open(json_path, "r") as f:
    spots = json.load(f)

# creating a copy of the original image to draw on
output_image = frame.copy()

# drawing quadrilaterals around parking spots 
for spot in spots:
    for key, coordinates in spot.items():  # have each spot 
        pts = np.array(coordinates, np.int32)  # conerting to np array
        pts = pts.reshape((-1, 1, 2))  # reshaping for opencv

        # darwing quadrilateral in blue
        cv2.polylines(output_image, [pts], isClosed=True, color=(255, 0, 0), thickness=2)

# displaying the final image 
cv2.imshow("Detected Parking Spots", output_image)
cv2.waitKey(0)
cv2.destroyAllWindows()
