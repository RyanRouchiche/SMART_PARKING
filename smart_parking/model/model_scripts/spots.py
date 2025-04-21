import cv2
import numpy as np
import json
import os
from ultralytics import YOLO

POINTS_FILE = "points.json"
CLICK_DISTANCE_THRESHOLD = 25

floor_number = "1"
spot_counter = 1
shapes_dict = {}  # {"Spot 1": {"points": [[x, y], ...], "occupied": 0}, ...}
current_shape = []

# Load the image
image_path = r"F:\downloads\pklot\train\images\2012-09-11_15_16_58_jpg.rf.61d961a86c9a16694403dfcb72cd450c.jpg"
image_original = cv2.imread(image_path)
if image_original is None:
    raise FileNotFoundError(f"Image not found at {image_path}")

image = image_original.copy()

# Load YOLO model
model = YOLO("weights/yolo11l.pt")


def ask_occupied_status():
    """Ask the user whether the spot is taken or not"""
    while True:
        val = input("Is the spot occupied? (1 for yes, 0 for no): ").strip()
        if val in ("0", "1"):
            return int(val)
        print("Invalid input. Please enter 1 or 0.")


def select_points(event, x, y, flags, param):
    global current_shape, image, spot_counter

    if event == cv2.EVENT_LBUTTONDOWN:
        current_shape.append((x, y))
        print(f"Point selected: {x}, {y}")

        if len(current_shape) == 4:
            label = f"Spot {spot_counter}"
            occupied = ask_occupied_status()
            shapes_dict[label] = {
                "points": current_shape[:],
                "occupied": occupied
            }
            spot_counter += 1
            draw_shapes()
            save_points()
            current_shape.clear()

    elif event == cv2.EVENT_RBUTTONDOWN:
        removed = remove_shape_near(x, y)
        if removed:
            print(f"Removed shape near ({x}, {y})")
            draw_shapes()
            save_points()


def draw_shapes():
    global image
    image = image_original.copy()
    for label, data in shapes_dict.items():
        points = data["points"]
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        color = (0, 0, 255) if data["occupied"] else (0, 255, 0)  # Red if taken, green if free
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=2)
        # Add label and status
        cx = int(np.mean([pt[0] for pt in points]))
        cy = int(np.mean([pt[1] for pt in points]))
        status = "Taken" if data["occupied"] else "Free"
        cv2.putText(image, f"{label} ({status})", (cx - 40, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.imshow("Initialization", image)


def remove_shape_near(x, y):
    """Remove the closest shape if the click is near any shape's point."""
    global shapes_dict
    for label, data in list(shapes_dict.items()):
        for px, py in data["points"]:
            if np.hypot(px - x, py - y) < CLICK_DISTANCE_THRESHOLD:
                del shapes_dict[label]
                return True
    return False


def save_points():
    try:
        data = [{
            "floor": floor_number,
            "coordinates": shapes_dict
        }]
        with open(POINTS_FILE, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Shapes saved to {POINTS_FILE}")
    except Exception as e:
        print(f"Error saving shapes: {e}")


def load_points():
    global shapes_dict, spot_counter
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, "r") as f:
                data = json.load(f)
                if data and "coordinates" in data[0]:
                    for k, v in data[0]["coordinates"].items():
                        shapes_dict[k] = {
                            "points": [tuple(pt) for pt in v["points"]],
                            "occupied": v["occupied"]
                        }
                    existing_spots = [int(name.split()[1]) for name in shapes_dict if name.startswith("Spot ")]
                    if existing_spots:
                        spot_counter = max(existing_spots) + 1
            print(f"Loaded {len(shapes_dict)} spots from {POINTS_FILE}")
            return True
        except Exception as e:
            print(f"Error reading saved shapes: {e}")
    return False


# Main execution
if load_points():
    draw_shapes()
else:
    cv2.imshow("Initialization", image)

cv2.setMouseCallback("Initialization", select_points)
cv2.waitKey(0)
cv2.destroyAllWindows()
