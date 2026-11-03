import re
from datetime import timedelta
from unittest import mock

from asgiref.sync import async_to_sync
from channels.testing import WebsocketCommunicator
from django.core import mail
from django.core.cache import cache
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase

from parking.models import Parking, ParkingMembership
from smart_parking.asgi import application
from .consumer import UserStatusConsumer
from .models import User, auth, hash_token

STRONG = "Gr33n-Parking-Lot!"


def register(client, **extra):
    data = {"username": "newowner", "password": STRONG, "email": "new@example.test", "first_name": "Ana"}
    data.update(extra)
    return client.post("/api/auth/register/", data, format="json")


class RegistrationTests(APITestCase):
    def setUp(self):
        cache.clear()

    def test_registration_never_grants_django_admin(self):
        self.assertEqual(register(self.client).status_code, 201)
        user = User.objects.get(username="newowner")
        self.assertFalse(user.is_superuser)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_active)

    def test_activation_email_escapes_the_name(self):
        register(self.client, first_name='<a href="https://evil.test">Verify</a>')
        body = mail.outbox[-1].body
        self.assertNotIn('<a href="https://evil.test">', body)
        self.assertIn("&lt;a href=", body)

    def test_taken_username_gets_the_same_answer(self):
        User.objects.create_user(username="taken", password=STRONG)
        first = register(self.client, username="taken")
        second = register(self.client, username="free-name")
        self.assertEqual((first.status_code, first.json()), (second.status_code, second.json()))
        self.assertIn("already taken", mail.outbox[0].body)
        self.assertIn("Verify Email", mail.outbox[1].body)

    def test_activation_link_works_once(self):
        register(self.client)
        link = re.search(r"/activate/([^/]+)/([^\"]+)", mail.outbox[-1].body)
        url = f"/api/auth/activate/{link.group(1)}/{link.group(2)}/"
        self.assertEqual(self.client.get(url).status_code, 200)
        User.objects.filter(username="newowner").update(is_active=False)
        self.assertEqual(self.client.get(url).status_code, 400)

    def test_weak_password_is_refused(self):
        self.assertEqual(register(self.client, password="123").status_code, 400)

    def test_registration_is_throttled(self):
        codes = [register(self.client, username=f"user{i}").status_code for i in range(6)]
        self.assertEqual(codes[-1], 429)


class SessionTests(APITestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="owner", password=STRONG)

    def test_logout_works_after_the_access_token_expired(self):
        self.client.post("/api/auth/login/", {"username": "owner", "password": STRONG}, format="json")
        later = timezone.now() + timedelta(minutes=2)
        with mock.patch("rest_framework_simplejwt.tokens.aware_utcnow", return_value=later):
            self.assertEqual(self.client.post("/api/auth/logout/").status_code, 200)
        self.assertTrue(auth.objects.get(user=self.user).is_revoked)
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def login(self):
        return self.client.post("/api/auth/login/", {"username": "owner", "password": STRONG}, format="json")

    def test_refresh_token_is_stored_hashed(self):
        self.login()
        cookie = self.client.cookies["refresh_token"].value
        self.assertEqual(auth.objects.get(user=self.user).token_hash, hash_token(cookie))
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 200)
        self.assertEqual(auth.objects.get(user=self.user).token_hash, hash_token(self.client.cookies["refresh_token"].value))

    def test_password_change_ends_the_refresh_chain(self):
        self.login()
        self.user.set_password("An0ther-Parking-Lot!")
        self.user.save()
        self.assertEqual(self.client.post("/api/auth/refresh/").status_code, 401)

    def test_cross_site_form_posts_are_refused(self):
        form = {"username": "owner", "password": STRONG}
        self.assertEqual(self.client.post("/api/auth/login/", form).status_code, 415)
        ParkingMembership.objects.create(user=self.user, parking=Parking.objects.create(name="A"), role="owner")
        self.client.force_authenticate(self.user)
        self.assertEqual(self.client.post("/api/users/", {"username": "x", "password": STRONG, "email": "x@example.test"}).status_code, 415)

    def test_malformed_public_input_returns_400(self):
        self.assertEqual(self.client.post("/api/auth/login/", [], format="json").status_code, 400)
        self.assertEqual(self.client.get("/api/auth/activate/bm90YXV1aWQ/x/").status_code, 400)


class SharedOperatorTests(APITestCase):
    def test_owner_only_removes_the_operator_from_their_parking(self):
        a, b = Parking.objects.create(name="A"), Parking.objects.create(name="B")
        owner_a = User.objects.create_user(username="owner-a", password=STRONG)
        shared = User.objects.create_user(username="shared", password=STRONG)
        ParkingMembership.objects.create(user=owner_a, parking=a, role="owner")
        ParkingMembership.objects.create(user=shared, parking=a, role="operator")
        ParkingMembership.objects.create(user=shared, parking=b, role="operator")
        self.client.force_authenticate(owner_a)

        self.assertEqual(self.client.delete(f"/api/users/{shared.id}/").status_code, 204)

        self.assertTrue(User.objects.filter(id=shared.id).exists())
        self.assertEqual(list(shared.memberships.values_list("parking__name", flat=True)), ["B"])


class PresenceTests(TransactionTestCase):
    def connect(self, user):
        communicator = WebsocketCommunicator(UserStatusConsumer.as_asgi(), "/ws/user-status/")
        communicator.scope["user"] = user
        return communicator

    def test_presence_stays_inside_the_parking(self):
        a, b = Parking.objects.create(name="A"), Parking.objects.create(name="B")
        owner_a = User.objects.create_user(username="owner-a")
        operator_b = User.objects.create_user(username="operator-b")
        ParkingMembership.objects.create(user=owner_a, parking=a, role="owner")
        ParkingMembership.objects.create(user=operator_b, parking=b, role="operator")

        async def scenario():
            watcher, other = self.connect(owner_a), self.connect(operator_b)
            await watcher.connect()
            await watcher.receive_json_from()
            await other.connect()
            leaked = not await watcher.receive_nothing(timeout=0.3)
            await other.disconnect()
            await watcher.disconnect()
            return leaked

        self.assertFalse(async_to_sync(scenario)())

    def test_foreign_origin_is_refused(self):
        async def scenario():
            communicator = WebsocketCommunicator(application, "/ws/user-status/", headers=[(b"origin", b"http://evil.example")])
            connected, _ = await communicator.connect()
            await communicator.disconnect()
            return connected

        self.assertFalse(async_to_sync(scenario)())
