import ipaddress
import os
import tempfile

from django.test import override_settings
from rest_framework.test import APITestCase

from parking.models import Parking, ParkingMembership
from users.models import User
from .models import Camera
from .services import camera_health
from .sources import open_source
from unittest import mock
from django.core.cache import cache


class CameraPathTests(APITestCase):
    def setUp(self):
        self.media = tempfile.mkdtemp()
        self.parking = Parking.objects.create(name="A")
        owner = User.objects.create_user(username="owner-a")
        ParkingMembership.objects.create(user=owner, parking=self.parking, role="owner")
        self.client.force_authenticate(owner)

    def post(self, path):
        with override_settings(CAMERA_MEDIA_ROOT=self.media):
            return self.client.post("/api/cameras/", [{"area": 1, "path": path, "ref": "CAM"}], format="json")

    def test_internal_and_foreign_sources_are_refused(self):
        for path in [
            "http://127.0.0.1:8001/predict",
            "rtsp://localhost/stream",
            "http://169.254.169.254/latest",
            "file:///etc/passwd",
            "concat:/etc/passwd",
            "/etc/passwd",
            "../other-parking/video.mp4",
        ]:
            self.assertEqual(self.post(path).status_code, 400, path)
        self.assertFalse(Camera.objects.exists())

    def test_camera_urls_and_parking_files_are_accepted(self):
        self.assertEqual(self.post("rtsp://192.168.1.20:554/stream").status_code, 201)
        res = self.post("lot.mp4")
        self.assertEqual(res.status_code, 201)
        expected = os.path.realpath(os.path.join(self.media, str(self.parking.id), "lot.mp4"))
        self.assertEqual(Camera.objects.get(path__endswith="lot.mp4").path, expected)

    def test_stored_internal_url_is_not_opened(self):
        self.assertFalse(open_source("http://127.0.0.1:8001/predict").isOpened())

    def test_camera_networks_allowlist(self):
        with override_settings(CAMERA_NETWORKS=[ipaddress.ip_network("192.168.10.0/24")]):
            self.assertEqual(self.post("rtsp://192.168.10.5/stream").status_code, 201)
            self.assertEqual(self.post("http://172.18.0.2:6379/").status_code, 400)
        self.assertEqual(self.post("http://[::ffff:127.0.0.1]:8001/").status_code, 400)

    def test_camera_health_is_probed_once_per_ttl(self):
        cache.clear()
        with mock.patch("camera.services.probe", return_value=True) as probe:
            self.assertEqual(camera_health(["a.mp4", "b.mp4"]), {"a.mp4": True, "b.mp4": True})
            self.assertEqual(camera_health(["a.mp4", "b.mp4"]), {"a.mp4": True, "b.mp4": True})
        self.assertEqual(probe.call_count, 2)
