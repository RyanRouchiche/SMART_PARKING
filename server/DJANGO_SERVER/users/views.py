import logging
from datetime import timedelta

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.tokens import default_token_generator
from django.db.models import Exists, OuterRef
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.timezone import now
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenRefreshView

from .models import User, auth
from .permission import IsAdmin
from .serializers import GuestSerializer, AdminSerializer, ListUserSerializer
from .utils import SETupCOOKIE, send_verif_email

logger = logging.getLogger(__name__)


def user_payload(user):
    return {
        'id': str(user.id),
        'username': user.username,
        'email': user.email,
        'role': user.user_type,
    }


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)

        user = authenticate(username=username, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'}, status=401)
        if not user.is_active:
            return Response({'error': 'Your account is invalid, check your email for validation'}, status=401)

        login(request, user)

        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        auth.objects.update_or_create(
            user=user,
            defaults={
                'refresh_token': refresh_token,
                'expires_at': now() + timedelta(hours=1),
                'is_revoked': False,
                'created_at': now(),
            }
        )

        res = Response({'user': user_payload(user)})
        SETupCOOKIE(res, 'access_token', access_token)
        SETupCOOKIE(res, 'refresh_token', refresh_token)
        return res


class RefreshView(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'Refresh token not found in cookies'}, status=401)

        token_obj = auth.objects.filter(refresh_token=refresh_token, is_revoked=False).first()
        if token_obj is None:
            return Response({'error': 'Refresh token is revoked or unknown'}, status=401)

        serializer = self.get_serializer(data={'refresh': refresh_token})
        try:
            serializer.is_valid(raise_exception=True)
        except (TokenError, InvalidToken) as e:
            logger.warning(f"Refresh failed: {e}")
            return Response({'error': 'Token is blacklisted or invalid'}, status=401)

        access_token = serializer.validated_data['access']
        new_refresh_token = serializer.validated_data['refresh']

        token_obj.refresh_token = new_refresh_token
        token_obj.expires_at = now() + timedelta(hours=1)
        token_obj.save(update_fields=['refresh_token', 'expires_at'])

        res = Response({'refreshed': True})
        SETupCOOKIE(res, 'access_token', access_token)
        SETupCOOKIE(res, 'refresh_token', new_refresh_token)
        return res


class LogoutView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if refresh_token:
            auth.objects.filter(refresh_token=refresh_token).update(is_revoked=True)
        logout(request)

        res = Response({'logged_out': True})
        res.delete_cookie('access_token')
        res.delete_cookie('refresh_token')
        return res


class MeView(APIView):
    def get(self, request):
        return Response({'user': user_payload(request.user)})


class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        send_verif_email(request, serializer.save())
        return Response({'message': 'Check your email for account activation'}, status=status.HTTP_201_CREATED)


class ActivateView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, uidb64, token):
        try:
            user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is None or not default_token_generator.check_token(user, token):
            return Response({'error': 'Invalid activation link.'}, status=400)

        user.is_active = True
        user.save(update_fields=['is_active'])
        return Response({'message': 'Account activated successfully!'})


class UserListView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request):
        users = User.objects.filter(user_type='guest').annotate(
            is_online=Exists(auth.objects.filter(user=OuterRef('pk'), is_revoked=False))
        )
        return Response({'users': ListUserSerializer(users, many=True).data})

    def post(self, request):
        serializer = GuestSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        send_verif_email(request, serializer.save())
        return Response({'message': 'Guest created, activation email sent'}, status=status.HTTP_201_CREATED)


class UserDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def delete(self, request, user_id):
        user = User.objects.filter(id=user_id).first()
        if user is None:
            return Response({'error': 'User not found'}, status=404)

        BlacklistedToken.objects.bulk_create(
            [BlacklistedToken(token=t) for t in OutstandingToken.objects.filter(user=user)],
            ignore_conflicts=True,
        )
        user.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
