from tensorflow.keras.preprocessing import image
from tensorflow.keras.models import load_model
import numpy as np
import time
import cv2

def predict_single_image(model, frame, target_size=(180, 180), threshold=0.5):
    
    image_rsized = cv2.resize(frame, target_size)
    img_array = image.img_to_array(image_rsized) / 255.0
    img_array = np.expand_dims(img_array, axis=0)
    start_time = time.time()
    prediction = model.predict(img_array, verbose=0)
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Prediction time for {image_rsized}: {elapsed_time:.4f} seconds")
    is_car = prediction[0][0] > threshold
    if is_car:
        return "occupied"
    else:
        return "empty"