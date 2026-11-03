import json
import re
import uuid
from unittest import mock

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from rest_framework.test import APITestCase
from rest_framework.throttling import AnonRateThrottle

from camera.models import Camera
from detection import state
from parking.models import Parking, ParkingMembership, Zone
from users.models import User
from .models import OwnerRequest

SQUARE = [[10, 10], [60, 10], [60, 60], [10, 60]]
ALGIERS = (36.7538, 3.0588)
NEARBY = "/api/public/v1/parkings/nearby/"


def offset(meters_north, meters_east=0):
    return ALGIERS[0] + meters_north / 111320, ALGIERS[1] + meters_east / 89300


def make_parking(name, north, published=True, zones=1, capacity=10):
    lat, lng = offset(north)
    parking = Parking.objects.create(name=name, address=f"{name} street", latitude=lat, longitude=lng, is_published=published, capacity=capacity, pricing_text="50 DA / h")
    for number in range(1, zones + 1):
        Zone.objects.create(parking=parking, number=number, spots={"Secret spot A": SQUARE, "Secret spot B": SQUARE})
        Camera.objects.create(parking=parking, area=number, path=f"/media/{name}-cam.mp4", ref="CAM")
    return parking


def fresh(parking, area, free, total=2):
    details = [{"spot": f"Secret spot {i}", "status": "empty" if i < free else "occupied"} for i in range(total)]
    state.store(parking.pk, area, {"area": area, "available_spots": free, "spot_details": details})


class NearbyTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.near = make_parking("Near", 300)
        self.middle = make_parking("Middle", 900, zones=2)
        make_parking("Hidden", 200, published=False)
        make_parking("Far", 20000)
        Parking.objects.create(name="Empty", latitude=ALGIERS[0], longitude=ALGIERS[1], is_published=True)
        fresh(self.near, 1, free=1)
        fresh(self.middle, 1, free=2)
        fresh(self.middle, 2, free=0)

    def tearDown(self):
        cache.clear()

    def get_nearby(self, **params):
        return self.client.get(NEARBY, {"lat": ALGIERS[0], "lng": ALGIERS[1], **params})

    def test_guests_get_published_parkings_sorted_by_distance(self):
        response = self.get_nearby()
        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual([r["name"] for r in results], ["Near", "Middle"])
        self.assertAlmostEqual(results[0]["distance_m"], 300, delta=5)
        self.assertEqual((results[0]["free"], results[0]["total"], results[0]["stale"]), (1, 2, False))
        self.assertEqual((results[1]["free"], results[1]["total"]), (2, 4))
        self.assertTrue(results[0]["updated_at"].endswith("Z"))

    def test_radius_limits_the_search(self):
        self.assertEqual([r["name"] for r in self.get_nearby(radius=500).json()["results"]], ["Near"])

    def test_missing_data_is_reported_as_stale_with_the_capacity(self):
        cache.clear()
        result = self.get_nearby().json()["results"][0]
        self.assertEqual((result["free"], result["total"], result["stale"], result["updated_at"]), (None, 10, True, None))

    def test_responses_never_expose_private_data(self):
        raw = json.dumps(self.get_nearby().json()) + json.dumps(self.client.get(f"/api/public/v1/parkings/{self.near.pk}/").json())
        for secret in ("Secret spot", "spot_details", "cam.mp4", "/media/", "CAM"):
            self.assertNotIn(secret, raw)

    def test_coordinates_are_validated(self):
        self.assertEqual(self.client.get(NEARBY, {"lng": 3}).status_code, 400)
        self.assertEqual(self.client.get(NEARBY, {"lat": 95, "lng": 3}).status_code, 400)
        self.assertEqual(self.get_nearby(radius=50000).status_code, 400)
        self.assertEqual(self.client.get(NEARBY, {"lat": "x", "lng": 3}).status_code, 400)

    def test_detail_shows_published_parkings_only(self):
        detail = self.client.get(f"/api/public/v1/parkings/{self.near.pk}/").json()
        self.assertEqual((detail["name"], detail["pricing_text"], detail["capacity"], detail["free"]), ("Near", "50 DA / h", 10, 1))
        hidden = Parking.objects.get(name="Hidden")
        self.assertEqual(self.client.get(f"/api/public/v1/parkings/{hidden.pk}/").status_code, 404)
        self.assertEqual(self.client.get(f"/api/public/v1/parkings/{uuid.uuid4()}/").status_code, 404)

    def test_eta_is_disabled_by_default(self):
        self.assertEqual(self.client.get("/api/public/v1/eta/").json(), {"enabled": False})

    def test_guests_are_rate_limited(self):
        with mock.patch.object(AnonRateThrottle, "THROTTLE_RATES", {"anon": "2/min", "user": "60/min"}):
            codes = [self.get_nearby().status_code for _ in range(3)]
        self.assertEqual(codes, [200, 200, 429])


class DriverAccountTests(APITestCase):
    def setUp(self):
        cache.clear()

    def register(self, username="driver1"):
        return self.client.post("/api/public/v1/auth/register/", {
            "username": username, "password": "Str0ng-pass-word", "email": f"{username}@example.dz",
            "first_name": "Amine", "last_name": "B", "language": "ar",
        }, format="json")

    def activate(self, username):
        user = User.objects.get(username=username)
        uid = re.search(r"/activate/([^/]+)/", mail.outbox[-1].body).group(1)
        self.client.get(f"/api/auth/activate/{uid}/{default_token_generator.make_token(user)}/")
        return User.objects.get(username=username)

    def login(self, username="driver1", password="Str0ng-pass-word"):
        return self.client.post("/api/public/v1/auth/login/", {"username": username, "password": password}, format="json")

    def test_full_driver_session(self):
        self.assertEqual(self.register().status_code, 201)
        driver = User.objects.get(username="driver1")
        self.assertEqual((driver.user_type, driver.is_active, driver.language, driver.is_staff), ("driver", False, "ar", False))
        self.assertEqual(self.login().status_code, 401)

        self.activate("driver1")
        tokens = self.login().json()
        self.assertEqual(tokens["user"]["language"], "ar")

        rotated = self.client.post("/api/public/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json")
        self.assertEqual(rotated.status_code, 200)
        self.assertEqual(self.client.post("/api/public/v1/auth/refresh/", {"refresh": tokens["refresh"]}, format="json").status_code, 401)

        self.client.post("/api/public/v1/auth/logout/", {"refresh": rotated.json()["refresh"]}, format="json")
        self.assertEqual(self.client.post("/api/public/v1/auth/refresh/", {"refresh": rotated.json()["refresh"]}, format="json").status_code, 401)

    def test_bearer_token_deletes_the_driver_account(self):
        self.register()
        self.activate("driver1")
        access = self.login().json()["access"]
        self.assertIn(self.client.delete("/api/public/v1/account/").status_code, (401, 403))
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        self.assertEqual(self.client.delete("/api/public/v1/account/").status_code, 204)
        self.assertFalse(User.objects.filter(username="driver1").exists())

    def test_owners_and_operators_must_use_the_web_app(self):
        owner = User.objects.create_user(username="owner", password="Str0ng-pass-word", user_type="admin", is_active=True)
        ParkingMembership.objects.create(user=owner, parking=Parking.objects.create(name="A"), role="owner")
        self.assertEqual(self.login("owner").status_code, 403)

    def test_registration_never_grants_staff_or_other_roles(self):
        self.client.post("/api/public/v1/auth/register/", {
            "username": "sneaky", "password": "Str0ng-pass-word", "email": "s@example.dz",
            "user_type": "admin", "is_staff": True, "is_superuser": True,
        }, format="json")
        user = User.objects.get(username="sneaky")
        self.assertEqual((user.user_type, user.is_staff, user.is_superuser), ("driver", False, False))


class SiteFormTests(APITestCase):
    REQUEST = {
        "name": "Karim", "company": "", "phone": "0550 12 34 56", "email": "karim@example.dz",
        "parking_name": "Parking Gare", "address": "Place de la Gare", "capacity": "120", "cameras": "4",
        "fiber": "yes", "message": "", "language": "ar", "consent": True, "website": "",
    }

    def setUp(self):
        cache.clear()

    def test_owner_request_is_stored_and_sent_to_the_team(self):
        response = self.client.post("/api/public/v1/owner-signup/", self.REQUEST, format="json")
        self.assertEqual(response.status_code, 201)
        saved = OwnerRequest.objects.get()
        self.assertEqual((saved.parking_name, saved.capacity, saved.fiber, saved.language, saved.status), ("Parking Gare", 120, "yes", "ar", "new"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Parking Gare", mail.outbox[0].subject)
        self.assertIn("0550 12 34 56", mail.outbox[0].body)

    def test_consent_and_contact_details_are_required(self):
        for field, value in (("consent", False), ("phone", "abc"), ("email", "no"), ("capacity", "-1")):
            response = self.client.post("/api/public/v1/owner-signup/", {**self.REQUEST, field: value}, format="json")
            self.assertEqual(response.status_code, 400, field)
        self.assertFalse(OwnerRequest.objects.exists())

    def test_honeypot_is_accepted_silently_and_ignored(self):
        response = self.client.post("/api/public/v1/owner-signup/", {**self.REQUEST, "website": "http://spam"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertFalse(OwnerRequest.objects.exists())
        self.assertEqual(mail.outbox, [])

    def test_the_request_survives_a_mail_failure(self):
        with mock.patch("public.services.send_mail", side_effect=OSError("smtp down")):
            response = self.client.post("/api/public/v1/owner-signup/", self.REQUEST, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertTrue(OwnerRequest.objects.exists())

    def test_contact_is_mailed_and_never_stored(self):
        response = self.client.post("/api/public/v1/contact/", {"name": "Lina", "email": "lina@example.dz", "message": "Bonjour"}, format="json")
        self.assertEqual(response.status_code, 201)
        self.assertIn("Bonjour", mail.outbox[0].body)
        self.assertFalse(OwnerRequest.objects.exists())
        with mock.patch("public.services.send_mail", side_effect=OSError("smtp down")):
            failed = self.client.post("/api/public/v1/contact/", {"name": "Lina", "email": "lina@example.dz", "message": "Bonjour"}, format="json")
        self.assertEqual(failed.status_code, 503)

    def test_site_forms_are_limited_per_address(self):
        codes = [self.client.post("/api/public/v1/contact/", {"name": "A", "email": "a@example.dz", "message": "x"}, format="json").status_code for _ in range(6)]
        self.assertEqual(codes[-1], 429)


class ThrottleIdentityTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_forged_forwarded_for_does_not_bypass_ip_limits(self):
        with mock.patch.object(AnonRateThrottle, "THROTTLE_RATES", {"anon": "2/min", "user": "60/min"}):
            codes = [
                self.client.get(NEARBY, {"lat": ALGIERS[0], "lng": ALGIERS[1]}, HTTP_X_FORWARDED_FOR=f"10.9.9.{i}, 203.0.113.7").status_code
                for i in range(3)
            ]
        self.assertEqual(codes, [200, 200, 429])

    def test_login_is_limited_per_username_across_addresses(self):
        codes = [
            self.client.post("/api/public/v1/auth/login/", {"username": "Victim", "password": f"guess{i}"}, format="json", HTTP_X_FORWARDED_FOR=f"198.51.100.{i}").status_code
            for i in range(6)
        ]
        self.assertEqual(codes, [401] * 5 + [429])
