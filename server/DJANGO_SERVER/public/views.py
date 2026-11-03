from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle, ScopedRateThrottle, SimpleRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework_simplejwt.authentication import JWTAuthentication

from users.interface import (
    DriverSerializer,
    InactiveAccount,
    InvalidCredentials,
    InvalidRefresh,
    authenticate_user,
    delete_account,
    issue_tokens,
    register_account,
    revoke,
    rotate_tokens,
)
from . import services
from .serializers import ContactSerializer, OwnerRequestSerializer

DRIVER = 'driver'
DEFAULT_RADIUS = 3000
MIN_RADIUS = 100
MAX_RADIUS = 10000


def number(params, name, low, high, default=None):
    raw = params.get(name)
    if raw is None and default is not None:
        return default
    try:
        value = float(raw)
    except (TypeError, ValueError):
        raise ValidationError({name: 'A number is required.'})
    if not low <= value <= high:
        raise ValidationError({name: f'Must be between {low} and {high}.'})
    return value


def driver_payload(user):
    return {'id': str(user.id), 'username': user.username, 'email': user.email, 'language': user.language}


class PublicAPIView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [AllowAny]
    throttle_classes = [AnonRateThrottle, UserRateThrottle]


class AuthAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'


def body(request):
    return request.data if isinstance(request.data, dict) else {}


class UsernameRateThrottle(SimpleRateThrottle):
    scope = 'login_user'

    def get_cache_key(self, request, view):
        username = body(request).get('username')
        if not isinstance(username, str) or not username:
            return None
        return self.cache_format % {'scope': self.scope, 'ident': username.strip().lower()}


class NearbyView(PublicAPIView):
    def get(self, request):
        lat = number(request.query_params, 'lat', -90, 90)
        lng = number(request.query_params, 'lng', -180, 180)
        radius = number(request.query_params, 'radius', MIN_RADIUS, MAX_RADIUS, DEFAULT_RADIUS)
        return Response({'results': services.nearby(lat, lng, radius)})


class ParkingDetailView(PublicAPIView):
    def get(self, request, parking_id):
        parking = services.detail(parking_id)
        if parking is None:
            return Response({'error': 'Parking not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(parking)


class EtaView(PublicAPIView):
    def get(self, request):
        return Response({'enabled': False})


class RegisterView(AuthAPIView):
    throttle_scope = 'register'

    def post(self, request):
        serializer = DriverSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        register_account(serializer, request)
        return Response({'message': 'Check your email for account activation'}, status=status.HTTP_201_CREATED)


class LoginView(AuthAPIView):
    throttle_classes = [ScopedRateThrottle, UsernameRateThrottle]

    def post(self, request):
        data = body(request)
        username, password = data.get('username'), data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)
        try:
            user = authenticate_user(username, password)
        except InvalidCredentials:
            return Response({'error': 'Invalid credentials'}, status=401)
        except InactiveAccount:
            return Response({'error': 'Your account is not activated, check your email'}, status=401)
        if user.user_type != DRIVER:
            return Response({'error': 'This account must use the web application'}, status=403)
        access, refresh = issue_tokens(user)
        return Response({'access': access, 'refresh': refresh, 'user': driver_payload(user)})


class RefreshView(AuthAPIView):
    def post(self, request):
        refresh = body(request).get('refresh')
        if not refresh:
            return Response({'error': 'Refresh token is required'}, status=400)
        try:
            access, refresh = rotate_tokens(refresh)
        except InvalidRefresh as e:
            return Response({'error': str(e)}, status=401)
        return Response({'access': access, 'refresh': refresh})


class LogoutView(AuthAPIView):
    def post(self, request):
        refresh = body(request).get('refresh')
        if refresh:
            revoke(refresh)
        return Response({'logged_out': True})


class SiteFormView(AuthAPIView):
    throttle_scope = 'register'

    def post(self, request):
        data = body(request)
        if data.get('website'):
            return Response({'received': True}, status=status.HTTP_201_CREATED)
        return self.handle(data)


class OwnerSignupView(SiteFormView):
    def handle(self, data):
        serializer = OwnerRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        services.submit_owner_request(serializer)
        return Response({'received': True}, status=status.HTTP_201_CREATED)


class ContactView(SiteFormView):
    def handle(self, data):
        serializer = ContactSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        try:
            services.send_contact(serializer.validated_data)
        except Exception:
            return Response({'error': 'The message could not be sent'}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        return Response({'received': True}, status=status.HTTP_201_CREATED)


class AccountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        if request.user.user_type != DRIVER:
            return Response({'error': 'This account must be deleted from the web application'}, status=403)
        delete_account(request.user.id)
        return Response(status=status.HTTP_204_NO_CONTENT)
