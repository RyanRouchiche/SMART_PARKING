import cv2
import numpy as np
import json
import os
from datetime import datetime
from tqdm import tqdm

parent_dir = r"F:\downloads\pklot\pklot2"
train_dir = r"train"
valid_dir = r"valid"
test_dir = r"test"
output_dir = r"F:\Github\SMART_PARKING\smart_parking\model\test_images"

os.makedirs(os.path.join(output_dir, "0"), exist_ok=True)
os.makedirs(os.path.join(output_dir, "1"), exist_ok=True)

with open(os.path.join(parent_dir, test_dir, "_annotations.coco.json"), "r") as f:
    data = json.load(f)

images = data["images"]
annotations = data["annotations"]


def open_image(image, n):
    for j, ann in enumerate(matching_boxes):
        if ann['category_id'] == n:
            x, y, w, h = map(int, ann['bbox'])
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            line = str(j+1)+ " " + str(ann['category_id'])
            cv2.putText(image, line, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 2)
        elif n == 0:
            x, y, w, h = map(int, ann['bbox'])
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
            line = str(j+1)+ " " + str(ann['category_id'])
            cv2.putText(image, line, (x, y - 15), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 0), 2)

    cv2.imshow(f"{i}", image)
    cv2.waitKey(0)

# def crop_image():
#     for j, ann in enumerate(matching_boxes):
#         x, y, w, h = map(int, ann['bbox'])
#         category_id = ann['category_id']
#         crop = image[y:y+h, x:x+w]

#         if category_id == 1:
#             output_path = os.path.join(output_dir, "0", f"{image_info['id']}_crop_{j}.jpg")
#             cv2.imwrite(output_path, crop)
#         elif category_id == 2:
#             output_path = os.path.join(output_dir, "1", f"{image_info['id']}_crop_{j}.jpg")
#             cv2.imwrite(output_path, crop)

i= 61
# for i in tqdm(range(len(images)), desc="Processing images", unit="image"):
image_info = images[i]
img_path = os.path.join(parent_dir, test_dir, image_info['file_name'])
image = cv2.imread(img_path)

matching_boxes = [ann for ann in annotations if ann['image_id'] == image_info['id']]
open_image(image, 0)
    # crop_image()