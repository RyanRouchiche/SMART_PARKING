import os
import shutil
from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np
from tqdm import tqdm
import threading

def predict_single_image(model, img_path, target_size=(180, 180), threshold=0.5):
    img = image.load_img(img_path, target_size=target_size)
    img_array = image.img_to_array(img) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    prediction = model.predict(img_array, verbose=0)
    return prediction[0][0] > threshold, prediction[0][0]

def predict_images_in_folder(model, folder_path, target_size=(180, 180), threshold=0.5,
                              no_car_output_folder=r'F:\Github\SMART_PARKING\smart_parking\model\model_images\valid_images\car'):
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.png')

    total_images = 0
    car_count = 0
    no_car_count = 0

    if not os.path.exists(no_car_output_folder):
        os.makedirs(no_car_output_folder)

    for filename in tqdm(os.listdir(folder_path), desc="Processing images (No Car)", unit="image"):
        if filename.lower().endswith(supported_formats):
            img_path = os.path.join(folder_path, filename)
            is_car, confidence = predict_single_image(model, img_path, target_size, threshold)

            total_images += 1
            if is_car:
                car_count += 1
            else:
                no_car_count += 1
                shutil.move(img_path, os.path.join(no_car_output_folder, filename))

    print("\n📊 Summary Report - No Car Images")
    print(f"Total images processed: {total_images}")
    print(f"Cars detected: {car_count}")
    print(f"No Cars detected: {no_car_count}")
    if total_images > 0:
        car_percent = (car_count / total_images) * 100
        print(f"Car %: {car_percent:.2f}%")

def copy_car_images(model, folder_path, target_size=(180, 180), threshold=0.5,
                    car_output_folder=r"F:\Github\SMART_PARKING\smart_parking\model\model_images\valid_images\nocar"):
    supported_formats = ('.jpg', '.jpeg', '.png', '.bmp', '.png')

    total_images = 0
    copied_count = 0

    if not os.path.exists(car_output_folder):
        os.makedirs(car_output_folder)

    for filename in tqdm(os.listdir(folder_path), desc="Processing images (Car)", unit="image"):
        if filename.lower().endswith(supported_formats):
            img_path = os.path.join(folder_path, filename)
            is_car, confidence = predict_single_image(model, img_path, target_size, threshold)

            total_images += 1
            if is_car:
                copied_count += 1
                shutil.move(img_path, os.path.join(car_output_folder, filename))

    print("\n✅ Car Images Move Report")
    print(f"Total images processed: {total_images}")
    print(f"Car images moved: {copied_count}")

# 🚀 Load model
model = load_model(r'D:\Games\car_classifier.keras')

# 🧵 Set up threading for parallel execution
no_car_thread = threading.Thread(
    target=predict_images_in_folder,
    args=(model, r'F:\Github\SMART_PARKING\smart_parking\model\model_images\valid_images\1')
)

car_thread = threading.Thread(
    target=copy_car_images,
    args=(model, r'F:\Github\SMART_PARKING\smart_parking\model\model_images\valid_images\0')
)

# ✅ Start both threads
no_car_thread.start()
car_thread.start()

# ⏳ Wait for both to finish
no_car_thread.join()
car_thread.join()

print("\n🏁 Both threads finished successfully!")
