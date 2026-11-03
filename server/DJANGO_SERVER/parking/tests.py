import importlib

from django.contrib.auth.models import AnonymousUser
from rest_framework.test import APITestCase

from camera.models import Camera
from users.models import User
from .access import zone_stream
from .models import Parking, ParkingMembership, Zone

pilot = importlib.import_module("parking.migrations.0002_pilot_parking")

SQUARE = [[10, 10], [60, 10], [60, 60], [10, 60]]


def make_user(name, user_type="guest"):
    return User.objects.create_user(username=name, password="x", user_type=user_type)


class PilotMigrationTests(APITestCase):
    def test_reads_the_committed_coordinates_file(self):
        areas = pilot.read_coordinates()
        self.assertEqual([a["area"] for a in areas], ["1"])
        self.assertEqual(len(areas[0]["coordinates"]), 3)

    def test_build_pilot_moves_spots_into_postgres(self):
        make_user("legacy-admin", "admin")
        make_user("legacy-guest", "guest")
        camera = Camera.objects.create(area=1, path="video.mp4", ref="CAM-01")
        areas = [{"area": "1", "coordinates": {"Spot 1": SQUARE, "Spot 2": SQUARE}}]

        parking = pilot.build_pilot(Parking, ParkingMembership, Zone, Camera, User, areas)

        zone = Zone.objects.get(parking=parking, number=1)
        self.assertEqual(zone.spots, {"Spot 1": SQUARE, "Spot 2": SQUARE})
        self.assertEqual(zone.camera, camera)
        self.assertEqual(parking.capacity, 2)
        camera.refresh_from_db()
        self.assertEqual(camera.parking, parking)
        roles = dict(ParkingMembership.objects.values_list("user__username", "role"))
        self.assertEqual(roles, {"legacy-admin": "owner", "legacy-guest": "operator"})

    def test_build_pilot_on_empty_install_creates_nothing(self):
        Parking.objects.all().delete()
        self.assertIsNone(pilot.build_pilot(Parking, ParkingMembership, Zone, Camera, User, []))
        self.assertFalse(Parking.objects.exists())


class ParkingAccessTests(APITestCase):
    def setUp(self):
        self.a = Parking.objects.create(name="A")
        self.b = Parking.objects.create(name="B")
        self.owner_a = make_user("owner-a", "admin")
        self.operator_a = make_user("operator-a")
        self.owner_b = make_user("owner-b", "admin")
        self.operator_b = make_user("operator-b")
        ParkingMembership.objects.create(user=self.owner_a, parking=self.a, role="owner")
        ParkingMembership.objects.create(user=self.operator_a, parking=self.a, role="operator")
        ParkingMembership.objects.create(user=self.owner_b, parking=self.b, role="owner")
        ParkingMembership.objects.create(user=self.operator_b, parking=self.b, role="operator")
        Zone.objects.create(parking=self.a, number=1, spots={"Spot 1": SQUARE})
        Zone.objects.create(parking=self.b, number=7, spots={"Spot 9": SQUARE})
        self.cam_a = Camera.objects.create(parking=self.a, area=1, path="missing-a.mp4", ref="CAM-A")
        self.cam_b = Camera.objects.create(parking=self.b, area=7, path="missing-b.mp4", ref="CAM-B")

    def as_user(self, user):
        self.client.force_authenticate(user)

    def test_anonymous_is_refused(self):
        for url in ["/api/parking/areas/", "/api/parking/coordinates/", "/api/cameras/", "/api/users/"]:
            self.assertIn(self.client.get(url).status_code, (401, 403), url)

    def test_members_only_see_their_parking(self):
        self.as_user(self.operator_a)
        self.assertEqual(self.client.get("/api/parking/areas/").json(), {"areas": [1]})
        data = self.client.get("/api/parking/coordinates/").json()["data"]
        self.assertEqual(data, [{"area": "1", "coordinates": {"Spot 1": SQUARE}}])

        self.as_user(self.owner_b)
        self.assertEqual(self.client.get("/api/parking/areas/").json(), {"areas": [7]})

    def test_other_parking_is_forbidden_even_by_id(self):
        self.as_user(self.owner_a)
        self.assertEqual(self.client.get(f"/api/parking/areas/?parking={self.b.id}").status_code, 403)
        self.assertEqual(self.client.get("/api/parking/areas/?parking=not-a-uuid").status_code, 403)
        self.assertEqual(self.client.get(f"/api/parking/areas/?parking={self.a.id}").status_code, 200)

    def test_owner_saves_spots_as_json_in_postgres(self):
        self.as_user(self.owner_a)
        shuffled = [[60, 60], [10, 10], [60, 10], [10, 60]]
        res = self.client.post("/api/parking/coordinates/", [{"area": "2", "coordinates": {"P01": shuffled}}], format="json")
        self.assertEqual(res.status_code, 201)
        zone = Zone.objects.get(parking=self.a, number=2)
        self.assertEqual(zone.spots, {"P01": [[10.0, 10.0], [60.0, 10.0], [60.0, 60.0], [10.0, 60.0]]})
        self.assertFalse(Zone.objects.filter(parking=self.b, number=2).exists())

    def test_operator_cannot_change_spots(self):
        self.as_user(self.operator_a)
        res = self.client.post("/api/parking/coordinates/", [{"area": "1", "coordinates": {"P01": SQUARE}}], format="json")
        self.assertEqual(res.status_code, 403)

    def test_cameras_are_scoped_to_owned_parking(self):
        self.as_user(self.owner_a)
        refs = [c["ref"] for c in self.client.get("/api/cameras/").json()["cameras"]]
        self.assertEqual(refs, ["CAM-A"])
        self.assertEqual(self.client.delete(f"/api/cameras/{self.cam_b.id}/").status_code, 404)
        self.assertTrue(Camera.objects.filter(id=self.cam_b.id).exists())

        self.as_user(self.operator_a)
        self.assertEqual(self.client.get("/api/cameras/").status_code, 403)

    def test_users_are_scoped_to_owned_parking(self):
        self.as_user(self.owner_a)
        names = [u["username"] for u in self.client.get("/api/users/").json()["users"]]
        self.assertEqual(names, ["operator-a"])
        self.assertEqual(self.client.delete(f"/api/users/{self.operator_b.id}/").status_code, 404)
        self.assertEqual(self.client.delete(f"/api/users/{self.owner_a.id}/").status_code, 404)
        self.assertTrue(User.objects.filter(id=self.operator_b.id).exists())

    def test_websocket_zone_lookup_checks_membership(self):
        self.assertEqual(zone_stream(self.operator_a, 1, None), self.a.pk)
        self.assertIsNone(zone_stream(self.operator_b, 1, None))
        self.assertIsNone(zone_stream(self.operator_a, 1, str(self.b.id)))
        self.assertIsNone(zone_stream(AnonymousUser(), 1, None))

    def test_coordinates_are_bounded(self):
        self.as_user(self.owner_a)
        huge = [[0, 0], [30000, 0], [30000, 30000], [0, 30000]]
        res = self.client.post("/api/parking/coordinates/", [{"area": "1", "coordinates": {"P01": huge}}], format="json")
        self.assertEqual(res.status_code, 400)
        many = {f"P{i}": SQUARE for i in range(501)}
        res = self.client.post("/api/parking/coordinates/", [{"area": "1", "coordinates": many}], format="json")
        self.assertEqual(res.status_code, 400)
