from django.http import StreamingHttpResponse as Sres, HttpResponse as res
from smart_parking.parking.logic.Camera import Camera
from parking.logic.CamConfig import get_ip_from_mac
import threading
import atexit


camera_lock = threading.Lock()
cam = None

def home(request):
    return res('This is smart parking')

def VideoStream(request):
    global cam
    if request.method == 'GET':
        with camera_lock:
            if cam is None:
                ip_address = get_ip_from_mac()
                cam = Camera(f"rtsp://admin:admin@{ip_address}:8554/Streaming/Channels/101")

        return Sres(
            cam.generateFrame(),
            content_type="multipart/x-mixed-replace; boundary=frame"
        )

# Fonction pour arrêter la caméra quand le serveur Django s'arrête
def stop_camera():
    global cam
    with camera_lock:
        if cam is not None:
            print("Arrêt de la caméra...")
            cam.stop()
            cam = None

atexit.register(stop_camera)
