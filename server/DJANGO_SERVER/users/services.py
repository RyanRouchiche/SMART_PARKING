from datetime import timedelta

from django.contrib.auth import authenticate
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Exists, OuterRef
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from django.utils.timezone import now
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.serializers import TokenRefreshSerializer
from rest_framework_simplejwt.settings import api_settings as jwt_settings
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.utils import get_md5_hash_password

from parking.models import ParkingMembership
from .emails import send_username_taken_email, send_verif_email
from .models import RefreshSession, User, hash_token

SESSION_LIFETIME = timedelta(hours=1)


class AuthError(Exception):
    pass


class InvalidCredentials(AuthError):
    pass


class InactiveAccount(AuthError):
    pass


class InvalidRefresh(AuthError):
    pass


def issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    RefreshSession.objects.update_or_create(
        user=user,
        defaults={
            'token_hash': hash_token(str(refresh)),
            'expires_at': now() + SESSION_LIFETIME,
            'is_revoked': False,
            'created_at': now(),
        },
    )
    return str(refresh.access_token), str(refresh)


def authenticate_user(username, password):
    user = authenticate(username=username, password=password)
    if not user:
        raise InvalidCredentials()
    if not user.is_active:
        raise InactiveAccount()
    return user


def password_unchanged(refresh_token, user):
    try:
        claim = RefreshToken(refresh_token).get(jwt_settings.REVOKE_TOKEN_CLAIM)
    except TokenError:
        return False
    return claim == get_md5_hash_password(user.password)


def rotate_tokens(refresh_token):
    session = RefreshSession.objects.filter(token_hash=hash_token(refresh_token), is_revoked=False).first()
    if session is None or not password_unchanged(refresh_token, session.user):
        raise InvalidRefresh('Refresh token is revoked or unknown')
    serializer = TokenRefreshSerializer(data={'refresh': refresh_token})
    try:
        serializer.is_valid(raise_exception=True)
    except (TokenError, InvalidToken) as e:
        raise InvalidRefresh('Token is blacklisted or invalid') from e
    access, refresh = serializer.validated_data['access'], serializer.validated_data['refresh']
    session.token_hash = hash_token(refresh)
    session.expires_at = now() + SESSION_LIFETIME
    session.save(update_fields=['token_hash', 'expires_at'])
    return access, refresh


def revoke(refresh_token):
    RefreshSession.objects.filter(token_hash=hash_token(refresh_token)).update(is_revoked=True)
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        pass


def register_owner(serializer, request):
    try:
        with transaction.atomic():
            user = serializer.save()
    except IntegrityError:
        send_username_taken_email(serializer.validated_data['email'])
    else:
        send_verif_email(request, user)


def activate_account(uidb64, token):
    try:
        user = User.objects.get(pk=force_str(urlsafe_base64_decode(uidb64)))
    except (TypeError, ValueError, OverflowError, ValidationError, User.DoesNotExist):
        return False
    if not default_token_generator.check_token(user, token):
        return False
    user.is_active = True
    user.last_login = now()
    user.save(update_fields=['is_active', 'last_login'])
    return True


def parking_operators(parking):
    return User.objects.filter(
        memberships__parking=parking, memberships__role=ParkingMembership.OPERATOR
    ).annotate(
        is_online=Exists(RefreshSession.objects.filter(user=OuterRef('pk'), is_revoked=False))
    )


def add_operator(serializer, parking, request):
    with transaction.atomic():
        operator = serializer.save()
        ParkingMembership.objects.create(user=operator, parking=parking, role=ParkingMembership.OPERATOR)
    send_verif_email(request, operator)


def remove_operator(user_id, owned_parkings):
    user = User.objects.filter(
        id=user_id, memberships__parking__in=owned_parkings, memberships__role=ParkingMembership.OPERATOR
    ).exclude(memberships__role=ParkingMembership.OWNER).first()
    if user is None:
        return False
    with transaction.atomic():
        ParkingMembership.objects.filter(
            user=user, parking__in=owned_parkings, role=ParkingMembership.OPERATOR
        ).delete()
        if not user.memberships.exists():
            BlacklistedToken.objects.bulk_create(
                [BlacklistedToken(token=t) for t in OutstandingToken.objects.filter(user=user)],
                ignore_conflicts=True,
            )
            user.delete()
    return True
