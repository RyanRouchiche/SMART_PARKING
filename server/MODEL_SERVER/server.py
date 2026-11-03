import io
import json
import os
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import numpy as np

from predictor import get_model, predict_spots

HOST = os.getenv("MODEL_SERVER_HOST", "127.0.0.1")
PORT = int(os.getenv("MODEL_SERVER_PORT", "8001"))
MAX_BODY = int(os.getenv("MODEL_SERVER_MAX_BODY", str(64 * 1024 * 1024)))
INFERENCE_SLOTS = threading.BoundedSemaphore(int(os.getenv("MODEL_SERVER_CONCURRENCY", "2")))


class Handler(BaseHTTPRequestHandler):
    def _json(self, status, payload):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path == "/health":
            return self._json(200, {"status": "ok"})
        self._json(404, {"error": "not found"})

    def do_POST(self):
        if self.path != "/predict":
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length <= 0 or length > MAX_BODY:
                return self._json(413, {"error": "body too large"})
            crops = np.load(io.BytesIO(self.rfile.read(length)), allow_pickle=False)
            if crops.ndim != 4 or crops.shape[-1] != 3 or crops.dtype != np.uint8:
                return self._json(400, {"error": "expected uint8 array of shape (N, H, W, 3)"})
            with INFERENCE_SLOTS:
                statuses = predict_spots(crops)
            self._json(200, {"statuses": statuses})
        except ValueError as e:
            self._json(400, {"error": str(e)})


if __name__ == "__main__":
    get_model()
    print(f"Model server listening on http://{HOST}:{PORT}")
    ThreadingHTTPServer((HOST, PORT), Handler).serve_forever()
