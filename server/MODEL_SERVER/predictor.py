import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from tensorflow.keras.models import load_model

MODEL_PATH = Path(__file__).resolve().parent / "car_classifier_2.keras"
BATCH_SIZE = int(os.getenv("MODEL_BATCH_SIZE", "64"))


@lru_cache(maxsize=None)
def get_model():
    return load_model(MODEL_PATH)


def classify(crops, threshold):
    batch = np.ascontiguousarray(crops[..., ::-1], dtype=np.float32)
    batch /= 255.0
    predictions = get_model()(batch, training=False).numpy()[:, 0]
    return ["occupied" if p > threshold else "empty" for p in predictions]


def predict_spots(crops, threshold=0.5):
    crops = np.asarray(crops)
    return [
        status
        for start in range(0, len(crops), BATCH_SIZE)
        for status in classify(crops[start:start + BATCH_SIZE], threshold)
    ]
