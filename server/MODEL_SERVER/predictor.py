from functools import lru_cache
from pathlib import Path

import cv2
import numpy as np
from tensorflow.keras.models import load_model

MODEL_PATH = Path(__file__).resolve().parent / "car_classifier_2.keras"


@lru_cache(maxsize=None)
def get_model():
    return load_model(MODEL_PATH)


def predict_spots(crops, threshold=0.5):
    batch = np.stack([cv2.cvtColor(crop, cv2.COLOR_BGR2RGB) for crop in crops]).astype("float32") / 255.0
    predictions = get_model()(batch, training=False).numpy()[:, 0]
    return ["occupied" if p > threshold else "empty" for p in predictions]
