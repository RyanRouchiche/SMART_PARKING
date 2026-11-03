import logging

from django.conf import settings
from django.contrib.auth import login, logout
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from . import services
from .serializers import AdminSerializer

logger = logging.getLogger(__name__)

ACCESS_COOKIE = 'access_token'
REFRESH_COOKIE = 'refresh_token'


def user_payload(user):
    return {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': user.user_type,
    }


def set_auth_cookies(response, access, refresh):
    for key, value in ((ACCESS_COOKIE, access), (REFRESH_COOKIE, refresh)):
        response.set_cookie(
            key=key,
            value=value,
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite='Strict',
            path='/',
        )
    return response


class PublicView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []


class LoginView(PublicView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'auth'

    def post(self, request):
        data = request.data if isinstance(request.data, dict) else {}
        username, password = data.get('username'), data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)
        try:
            user = services.authenticate_user(username, password)
        except services.InvalidCredentials:
            return Response({'error': 'Invalid credentials'}, status=401)
        except services.InactiveAccount:
            return Response({'error': 'Your account is invalid, check your email for validation'}, status=401)

        login(request, user)
        return set_auth_cookies(Response({'user': user_payload(user)}), *services.issue_tokens(user))


class RefreshView(PublicView):
    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        if not refresh_token:
            return Response({'error': 'Refresh token not found in cookies'}, status=401)
        try:
            tokens = services.rotate_tokens(refresh_token)
        except services.InvalidRefresh as e:
            logger.warning(f"Refresh failed: {e.__cause__ or e}")
            return Response({'error': str(e)}, status=401)
        return set_auth_cookies(Response({'refreshed': True}), *tokens)


class LogoutView(PublicView):
    def post(self, request):
        refresh_token = request.COOKIES.get(REFRESH_COOKIE)
        if refresh_token:
            services.revoke(refresh_token)
        logout(request)

        res = Response({'logged_out': True})
        res.delete_cookie(ACCESS_COOKIE)
        res.delete_cookie(REFRESH_COOKIE)
        return res


class MeView(APIView):
    def get(self, request):
        return Response({'user': user_payload(request.user)})


class RegisterView(PublicView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = 'register'

    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        services.register_owner(serializer, request)
        return Response({'message': 'Check your email for account activation'}, status=status.HTTP_201_CREATED)


class ActivateView(PublicView):
    def get(self, request, uidb64, token):
        if not services.activate_account(uidb64, token):
            return Response({'error': 'Invalid activation link.'}, status=400)
        return Response({'message': 'Account activated successfully!'})
