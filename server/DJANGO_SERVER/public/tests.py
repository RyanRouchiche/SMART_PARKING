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
from parking.models import Parking, ParkingMembership, Subscription, Zone
from users.models import User
from . import services
from detection.events import announce_if_freed
from detection.interface import AVAILABILITY_STREAM, stream_client
from . import notifications
from .models import DriverDevice, Favorite, OwnerRequest

SQUARE = [[10, 10], [60, 10], [60, 60], [10, 60]]
ALGIERS = (36.7538, 3.0588)
NEARBY = "/api/public/v1/parkings/nearby/"


def offset(meters_north, meters_east=0):
    return ALGIERS[0] + meters_north / 111320, ALGIERS[1] + meters_east / 89300


def make_parking(name, north, published=True, zones=1, capacity=10, subscription=Subscription.ACTIVE):
    lat, lng = offset(north)
    parking = Parking.objects.create(name=name, address=f"{name} street", latitude=lat, longitude=lng, is_published=published, capacity=capacity, pricing_text="50 DA / h")
    Subscription.objects.filter(parking=parking).update(status=subscription)
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

    def test_only_subscribed_parkings_are_listed(self):
        for status in (Subscription.REQUEST, Subscription.CANCELLED, Subscription.PAST_DUE, Subscription.TRIAL):
            make_parking(status, 500, subscription=status)
        names = {p["name"] for p in self.client.get(NEARBY, {"lat": ALGIERS[0], "lng": ALGIERS[1]}).json()["results"]}
        self.assertEqual(names, {"Near", "Middle", Subscription.PAST_DUE, Subscription.TRIAL})

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

    def login(self, password, address):
        return self.client.post("/api/public/v1/auth/login/", {"username": "Victim", "password": password}, format="json", HTTP_X_FORWARDED_FOR=address).status_code

    def test_failed_logins_are_limited_per_username_and_address(self):
        codes = [self.login(f"guess{i}", "198.51.100.7") for i in range(6)]
        self.assertEqual(codes, [401] * 5 + [429])

    def test_an_attacker_cannot_lock_out_the_real_driver(self):
        User.objects.create_user(username="Victim", password="Str0ng-pass-word", user_type="driver", is_active=True)
        attacker = [self.login(f"guess{i}", "203.0.113.66") for i in range(6)]
        self.assertEqual(attacker[-1], 429)
        self.assertEqual(self.login("Str0ng-pass-word", "203.0.113.66"), 429)
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.20"), 200)

    def test_a_successful_login_resets_the_failures(self):
        User.objects.create_user(username="Victim", password="Str0ng-pass-word", user_type="driver", is_active=True)
        for i in range(4):
            self.login(f"guess{i}", "198.51.100.30")
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.30"), 200)
        self.assertEqual([self.login(f"again{i}", "198.51.100.30") for i in range(5)], [401] * 5)


class DistributedGuessingTests(APITestCase):
    def setUp(self):
        cache.clear()
        User.objects.create_user(username="Victim", password="Str0ng-pass-word", user_type="driver", is_active=True)

    def login(self, password, address):
        return self.client.post("/api/public/v1/auth/login/", {"username": "Victim", "password": password}, format="json", HTTP_X_FORWARDED_FOR=address).status_code

    def test_many_addresses_hit_an_account_wide_cap(self):
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.1"), 200)
        codes = [self.login(f"guess{i}", f"203.0.113.{i}") for i in range(30)]
        self.assertEqual(set(codes), {401})
        self.assertEqual(self.login("Str0ng-pass-word", "203.0.113.200"), 429)
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.1"), 200)

    def test_attempts_are_counted_before_the_password_check(self):
        results = [services.start_login("Victim", "192.0.2.9") for _ in range(6)]
        self.assertEqual(results, [True] * 5 + [False])

    def test_refused_attempts_do_not_fill_the_account_cap(self):
        for i in range(40):
            self.login(f"guess{i}", "203.0.113.77")
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.50"), 200)

    def test_crafted_usernames_cannot_reach_another_drivers_counters(self):
        for i in range(10):
            self.client.post("/api/public/v1/auth/login/", {"username": "Victim:198.51.100.60", "password": f"x{i}"}, format="json", HTTP_X_FORWARDED_FOR=f"203.0.113.{i}")
        self.assertEqual(self.login("Str0ng-pass-word", "198.51.100.60"), 200)

    def test_another_spelling_does_not_share_the_known_address(self):
        User.objects.create_user(username="victim", password="Other-pass-word1", user_type="driver", is_active=True)
        self.assertEqual(self.client.post("/api/public/v1/auth/login/", {"username": "victim", "password": "Other-pass-word1"}, format="json", HTTP_X_FORWARDED_FOR="203.0.113.150").status_code, 200)
        for i in range(30):
            self.login(f"guess{i}", f"203.0.113.{i}")
        self.assertEqual(self.login("Str0ng-pass-word", "203.0.113.150"), 429)


class OwnerRequestAcceptanceTests(APITestCase):
    def request(self, email="Owner@Example.com"):
        return OwnerRequest.objects.create(
            name="Amine", phone="0555 12 34 56", email=email, parking_name="Parking Port",
            address="Rue du Port", capacity=40, cameras=2,
        )

    def test_without_an_owner_account_nothing_is_created(self):
        User.objects.create_user(username="drv", email="owner@example.com", password="x", user_type="driver", is_active=True)
        User.objects.create_user(username="sleepy", email="owner@example.com", password="x", user_type="admin", is_active=False)
        owner_request = self.request()
        self.assertIsNone(services.accept_owner_request(owner_request))
        self.assertFalse(Parking.objects.filter(name="Parking Port").exists())
        owner_request.refresh_from_db()
        self.assertEqual(owner_request.status, "new")

    def test_accepting_creates_a_draft_parking_for_the_owner(self):
        owner = User.objects.create_user(username="boss", email="owner@example.com", password="x", user_type="admin", is_active=True)
        owner_request = self.request()

        parking = services.accept_owner_request(owner_request)

        self.assertEqual((parking.name, parking.address, parking.capacity, parking.is_published), ("Parking Port", "Rue du Port", 40, False))
        self.assertTrue(ParkingMembership.objects.filter(user=owner, parking=parking, role="owner").exists())
        self.assertEqual(parking.subscription.status, Subscription.REQUEST)
        owner_request.refresh_from_db()
        self.assertEqual((owner_request.status, owner_request.parking), ("accepted", parking))


class FakeSender:
    def __init__(self, invalid=()):
        self.sent = []
        self.invalid = set(invalid)

    def send(self, token, title, body, data):
        if token in self.invalid:
            raise notifications.InvalidToken()
        self.sent.append((token, title, body, data))


class FavoritesAndDevicesTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.parking = make_parking("Near", 300)
        self.hidden = make_parking("Hidden", 200, published=False)
        self.driver = User.objects.create_user(username="d1", password="x", user_type="driver", is_active=True)
        self.other = User.objects.create_user(username="d2", password="x", user_type="driver", is_active=True)
        self.client.force_authenticate(self.driver)

    def tearDown(self):
        cache.clear()

    def url(self, parking):
        return f"/api/public/v1/favorites/{parking.pk}/"

    def test_favorites_are_personal_and_limited_to_published_parkings(self):
        fresh(self.parking, 1, free=1)
        response = self.client.put(self.url(self.parking), {"notify": True}, format="json")
        self.assertEqual(response.json(), {"id": str(self.parking.pk), "notify": True})
        self.assertEqual(self.client.put(self.url(self.hidden), {}, format="json").status_code, 404)

        results = self.client.get("/api/public/v1/favorites/").json()["results"]
        self.assertEqual([(r["name"], r["notify"], r["free"]) for r in results], [("Near", True, 1)])
        self.assertNotIn("Secret spot A", json.dumps(results))

        self.client.force_authenticate(self.other)
        self.assertEqual(self.client.get("/api/public/v1/favorites/").json()["results"], [])
        self.assertEqual(self.client.delete(self.url(self.parking)).status_code, 404)
        self.client.force_authenticate(self.driver)
        self.assertEqual(self.client.delete(self.url(self.parking)).status_code, 204)

    def test_only_signed_in_drivers_use_favorites_and_devices(self):
        owner = User.objects.create_user(username="boss", password="x", user_type="admin", is_active=True)
        self.client.force_authenticate(owner)
        self.assertEqual(self.client.get("/api/public/v1/favorites/").status_code, 403)
        self.client.force_authenticate(None)
        self.assertEqual(self.client.get("/api/public/v1/favorites/").status_code, 401)
        devices = self.client.post("/api/public/v1/devices/", {"token": "t", "platform": "android"}, format="json")
        self.assertEqual(devices.status_code, 401)

    def test_a_phone_token_follows_the_driver_who_signs_in(self):
        devices = "/api/public/v1/devices/"
        self.assertEqual(self.client.post(devices, {"token": "phone-1"}, format="json").status_code, 400)
        self.assertEqual(self.client.post(devices, {"token": "phone-1", "platform": "android"}, format="json").status_code, 204)
        self.client.force_authenticate(self.other)
        self.client.post(devices, {"token": "phone-1", "platform": "android"}, format="json")
        self.assertEqual(list(DriverDevice.objects.values_list("user__username", flat=True)), ["d2"])

        self.client.force_authenticate(self.driver)
        self.client.delete(devices, {"token": "phone-1"}, format="json")
        self.assertTrue(DriverDevice.objects.filter(token="phone-1").exists())
        self.client.force_authenticate(self.other)
        self.client.delete(devices, {"token": "phone-1"}, format="json")
        self.assertFalse(DriverDevice.objects.exists())


class NotificationTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.parking = make_parking("Near", 300)
        users = [
            User.objects.create_user(username=name, password="x", user_type="driver", is_active=True, language=lang)
            for name, lang in (("fr", "fr"), ("ar", "ar"), ("quiet", "fr"))
        ]
        for user, notify in zip(users, (True, True, False)):
            Favorite.objects.create(user=user, parking=self.parking, notify=notify)
            DriverDevice.objects.create(user=user, token=f"tok-{user.username}", platform="android")

    def tearDown(self):
        cache.clear()

    def test_drivers_who_asked_are_notified_once_per_30_minutes_in_their_language(self):
        sender = FakeSender()
        self.assertEqual(notifications.notify_freed(str(self.parking.pk), 3, sender), 2)
        self.assertEqual(notifications.notify_freed(str(self.parking.pk), 4, sender), 0)
        bodies = {token: (title, body) for token, title, body, _ in sender.sent}
        self.assertEqual(set(bodies), {"tok-fr", "tok-ar"})
        self.assertEqual(bodies["tok-fr"], ("Des places se libèrent", "Near : 3 place(s) libre(s) maintenant."))
        self.assertIn("أماكن", bodies["tok-ar"][0])
        self.assertEqual(sender.sent[0][3], {"parking_id": str(self.parking.pk)})

    def test_invalid_tokens_are_removed(self):
        notifications.notify_freed(str(self.parking.pk), 1, FakeSender(invalid={"tok-fr"}))
        self.assertFalse(DriverDevice.objects.filter(token="tok-fr").exists())
        self.assertTrue(DriverDevice.objects.filter(token="tok-ar").exists())

    def test_hidden_parkings_send_nothing(self):
        Subscription.objects.filter(parking=self.parking).update(status=Subscription.CANCELLED)
        self.assertEqual(notifications.notify_freed(str(self.parking.pk), 1, FakeSender()), 0)

    def test_worker_reads_freed_events_from_the_stream(self):
        client = stream_client()
        client.delete(AVAILABILITY_STREAM)
        notifications.ensure_group(client)
        notifications.ensure_group(client)
        fresh(self.parking, 1, free=0)
        self.assertFalse(announce_if_freed(str(self.parking.pk), [1], client))
        fresh(self.parking, 1, free=2)
        self.assertTrue(announce_if_freed(str(self.parking.pk), [1], client))
        sender = FakeSender()
        self.assertEqual(notifications.process(client, sender, "test", block_ms=100), 1)
        self.assertEqual(len(sender.sent), 2)
        self.assertEqual(notifications.process(client, sender, "test", block_ms=100), 0)
        client.delete(AVAILABILITY_STREAM)
