import importlib
from datetime import date, timedelta
from io import StringIO

from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.management import call_command
from django.test import TestCase, override_settings
from rest_framework.test import APITestCase

from camera.models import Camera
from users.models import User
from .access import stream_parking
from .models import Invoice, Parking, ParkingMembership, Subscription, Zone
from .services import all_zone_layouts
from .subscriptions import add_months, run_daily, start_trial

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
        self.assertEqual(stream_parking(self.operator_a, 1, None), self.a.pk)
        self.assertIsNone(stream_parking(self.operator_b, 1, None))
        self.assertIsNone(stream_parking(self.operator_a, 1, str(self.b.id)))
        self.assertIsNone(stream_parking(AnonymousUser(), 1, None))

    def test_coordinates_are_bounded(self):
        self.as_user(self.owner_a)
        huge = [[0, 0], [30000, 0], [30000, 30000], [0, 30000]]
        res = self.client.post("/api/parking/coordinates/", [{"area": "1", "coordinates": {"P01": huge}}], format="json")
        self.assertEqual(res.status_code, 400)
        many = {f"P{i}": SQUARE for i in range(501)}
        res = self.client.post("/api/parking/coordinates/", [{"area": "1", "coordinates": many}], format="json")
        self.assertEqual(res.status_code, 400)


TODAY = date(2026, 11, 30)


@override_settings(TRIAL_MONTHS=3, GRACE_DAYS=15, TEAM_EMAIL="team@example.com")
class SubscriptionTests(TestCase):
    def subscribed(self, name, status, period_end):
        parking = Parking.objects.create(name=name)
        Subscription.objects.filter(parking=parking).update(status=status, period_end=period_end)
        return Subscription.objects.get(parking=parking)

    def test_new_parkings_start_as_a_request(self):
        self.assertEqual(Parking.objects.create(name="New").subscription.status, Subscription.REQUEST)

    def test_months_are_added_without_overflowing_the_month(self):
        self.assertEqual(add_months(TODAY, 3), date(2027, 2, 28))
        self.assertEqual(add_months(date(2026, 1, 15), 12), date(2027, 1, 15))

    def test_trial_lasts_the_configured_months(self):
        subscription = Parking.objects.create(name="New").subscription
        start_trial(subscription, TODAY)
        subscription.refresh_from_db()
        self.assertEqual((subscription.status, subscription.period_end), (Subscription.TRIAL, date(2027, 2, 28)))

    def test_expiry_then_grace_then_cancellation(self):
        ended = self.subscribed("Ended", Subscription.TRIAL, TODAY - timedelta(days=1))
        grace = self.subscribed("Grace", Subscription.PAST_DUE, TODAY - timedelta(days=15))
        lapsed = self.subscribed("Lapsed", Subscription.PAST_DUE, TODAY - timedelta(days=16))
        open_ended = self.subscribed("Pilot", Subscription.ACTIVE, None)

        self.assertEqual(run_daily(TODAY), {"expired": 1, "cancelled": 1, "reminded": 0})

        statuses = {s.parking.name: s.status for s in Subscription.objects.select_related("parking")}
        self.assertEqual(statuses[ended.parking.name], Subscription.PAST_DUE)
        self.assertEqual(statuses[grace.parking.name], Subscription.PAST_DUE)
        self.assertEqual(statuses[lapsed.parking.name], Subscription.CANCELLED)
        self.assertEqual(statuses[open_ended.parking.name], Subscription.ACTIVE)

    def test_owners_are_reminded_30_and_7_days_before_in_their_language(self):
        for days, language in ((30, "fr"), (7, "ar"), (8, "fr")):
            subscription = self.subscribed(f"P{days}", Subscription.ACTIVE, TODAY + timedelta(days=days))
            owner = User.objects.create_user(username=f"owner{days}", email=f"o{days}@example.com", password="x", language=language)
            ParkingMembership.objects.create(user=owner, parking=subscription.parking, role="owner")
        operator = User.objects.create_user(username="op", email="op@example.com", password="x")
        ParkingMembership.objects.create(user=operator, parking=Parking.objects.get(name="P30"), role="operator")

        self.assertEqual(run_daily(TODAY)["reminded"], 2)

        sent = {m.to[0]: m.subject for m in mail.outbox}
        self.assertEqual(set(sent), {"o30@example.com", "o7@example.com"})
        self.assertIn("se termine", sent["o30@example.com"])
        self.assertIn("ينتهي", sent["o7@example.com"])

    def test_a_paid_invoice_activates_and_extends_the_subscription(self):
        subscription = self.subscribed("Paying", Subscription.PAST_DUE, TODAY - timedelta(days=3))
        Invoice.objects.create(subscription=subscription, reference="F-1", amount_da=5000, period_end=date(2027, 11, 30))
        subscription.refresh_from_db()
        self.assertEqual(subscription.status, Subscription.PAST_DUE)

        invoice = Invoice.objects.get(reference="F-1")
        invoice.paid_on = TODAY
        invoice.save()
        subscription.refresh_from_db()
        self.assertEqual((subscription.status, subscription.period_end), (Subscription.ACTIVE, date(2027, 11, 30)))

    def test_cancelled_parkings_are_no_longer_watched(self):
        kept = self.subscribed("Kept", Subscription.REQUEST, None)
        gone = self.subscribed("Gone", Subscription.CANCELLED, None)
        for subscription in (kept, gone):
            Zone.objects.create(parking=subscription.parking, number=1, spots={"Spot 1": SQUARE})
        watched = {z[0] for z in all_zone_layouts()}
        self.assertIn(kept.parking_id, watched)
        self.assertNotIn(gone.parking_id, watched)

    def test_daily_command_reports_what_it_did(self):
        out = StringIO()
        call_command("subscriptions_daily", stdout=out)
        self.assertIn("expired=0 cancelled=0 reminded=0", out.getvalue())
