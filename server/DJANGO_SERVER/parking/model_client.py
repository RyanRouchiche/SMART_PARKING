import io
import json
import urllib.request

import numpy as np
from django.conf import settings


def predict_spots(crops):
    buffer = io.BytesIO()
    np.save(buffer, np.stack(crops))
    request = urllib.request.Request(
        f"{settings.MODEL_SERVER_URL}/predict",
        data=buffer.getvalue(),
        headers={"Content-Type": "application/octet-stream"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.load(response)["statuses"]
