import os
import shutil
from tqdm import tqdm
from ultralytics import YOLO

# CONFIG
SOURCE_FOLDER = r"F:\Github\SMART_PARKING\smart_parking\model\model_images\0"
CAR_FOLDER = r"F:\Github\SMART_PARKING\smart_parking\model\model_images\0"
NO_CAR_FOLDER = r"F:\Github\SMART_PARKING\smart_parking\model\model_images\1"
CAR_THRESHOLD = 0.9  # 90% confidence

# Prepare destination folders
os.makedirs(CAR_FOLDER, exist_ok=True)
os.makedirs(NO_CAR_FOLDER, exist_ok=True)

# Load pre-trained YOLOv8 model
model = YOLO(r"F:\Github\SMART_PARKING\smart_parking\model\model_scripts\Weights\yolo11n.pt")  # You can switch to yolov8s.pt or yolov8m.pt if you want better accuracy

# Get list of image files
image_files = [f for f in os.listdir(SOURCE_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# Main loop with progress bar
for filename in tqdm(image_files, desc="Processing images"):
    full_path = os.path.join(SOURCE_FOLDER, filename)
    try:
        results = model(full_path, verbose=False)
        detections = results[0].boxes
        car_detected = False

        for box in detections:
            cls = int(box.cls.item())
            conf = float(box.conf.item())
            name = results[0].names[cls]

            if name == "car" and conf >= CAR_THRESHOLD:
                car_detected = True
                break

        if car_detected:
            shutil.move(full_path, os.path.join(CAR_FOLDER, filename))
        else:
            shutil.move(full_path, os.path.join(NO_CAR_FOLDER, filename))

    except Exception as e:
        print(f"Error processing {filename}: {e}")