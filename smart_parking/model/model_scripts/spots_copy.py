import cv2
import numpy as np
import json
import os
POINTS_FILE = "points.json"
CLICK_DISTANCE_THRESHOLD = 25

floor_number = "1"
spot_counter = 1
shapes_dict = {}
current_shape = []
hovered_spot = None
mouse_position = (0, 0)

# Load the image
with open("image_path.txt", "r") as f:
    image_name = f.read().strip()
image_path = r"F:\downloads\pklot\train\images"
image_path = os.path.join(image_path, image_name)
image_path = image_path + ".jpg"
image_original = cv2.imread(image_path)
if image_original is None:
    raise FileNotFoundError(f"Image not found at {image_path}")

image = image_original.copy()

# Load YOLO model
# model = YOLO("weights/yolo11l.pt")

# Function to select points on the image to define parking spots
def select_points(event, x, y, flags, param):
    global current_shape, image, spot_counter, mouse_position
    mouse_position = (x, y)

    if event == cv2.EVENT_LBUTTONDOWN:
        current_shape.append((x, y))
        print(f"Point selected: {x}, {y}")

        if len(current_shape) == 4:
            label = f"Spot {spot_counter}"
            shapes_dict[label] = {
                "points": current_shape[:],
                "occupied": 0
            }
            spot_counter += 1
            current_shape.clear()
            draw_shapes()
            save_points()

    elif event == cv2.EVENT_RBUTTONDOWN:
        removed = remove_shape_near(x, y)
        if removed:
            print(f"Removed shape near ({x}, {y})")
            draw_shapes()
            save_points()

# function to draw shapes on the image
def draw_shapes():
    global image, hovered_spot
    image = image_original.copy()
    hovered_spot = get_hovered_spot(*mouse_position)

    for label, data in shapes_dict.items():
        points = data["points"]
        pts = np.array(points, np.int32).reshape((-1, 1, 2))
        is_hovered = label == hovered_spot
        color = (0, 255, 255) if is_hovered else ((0, 0, 255) if data["occupied"] else (0, 255, 0))
        cv2.polylines(image, [pts], isClosed=True, color=color, thickness=2)

        cx = int(np.mean([pt[0] for pt in points]))
        cy = int(np.mean([pt[1] for pt in points]))
        name = label.split()[1]
        cv2.putText(image, f"{name}", (cx - 5, cy), cv2.FONT_HERSHEY_SIMPLEX, 0.40, color, 2)

    cv2.imshow("Initialization", image)

# Get the hovered spot based on mouse position
def get_hovered_spot(x, y):
    best_label = None
    best_distance = -1

    for label, data in shapes_dict.items():
        pts = np.array(data["points"], np.int32).reshape((-1, 1, 2))
        dist = cv2.pointPolygonTest(pts, (x, y), measureDist=True)
        if dist > best_distance:
            best_distance = dist
            best_label = label

    return best_label if best_distance >= 0 else None

# Remove shape near the clicked point
def remove_shape_near(x, y):
    global shapes_dict
    for label, data in list(shapes_dict.items()):
        pts = np.array(data["points"], np.int32).reshape((-1, 1, 2))
        result = cv2.pointPolygonTest(pts, (x, y), measureDist=False)
        if result >= 0:
            del shapes_dict[label]
            return True
    return False


# Save the shapes to a JSON file
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

# laod the shapes from the JSON file
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

# Action Handler for keypresses
def handle_keypress():
    global hovered_spot
    key = cv2.waitKey(1) & 0xFF
    if key == ord('t') and hovered_spot:
        shapes_dict[hovered_spot]["occupied"] = 1
        print(f"{hovered_spot} marked as Taken.")
        draw_shapes()
        save_points()
    elif key == ord('f') and hovered_spot:
        shapes_dict[hovered_spot]["occupied"] = 0
        print(f"{hovered_spot} marked as Free.")
        draw_shapes()
        save_points()
    elif key == 27:  # ESC key to close the window
        cv2.destroyAllWindows()
        exit()


# Main execution
if load_points():
    cv2.namedWindow("Initialization", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Initialization", 1600, 900)
    draw_shapes()
else:
    cv2.namedWindow("Initialization", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Initialization", 1600, 900)
    cv2.imshow("Initialization", image)

cv2.setMouseCallback("Initialization", select_points)

while True:
    handle_keypress()
    draw_shapes()
