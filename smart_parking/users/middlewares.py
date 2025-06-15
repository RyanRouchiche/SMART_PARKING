from django.shortcuts import redirect
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.backends import TokenBackend
from django.conf import settings

class InvalidJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.token_backend = TokenBackend(
            algorithm='HS256',
            signing_key=settings.SECRET_KEY
        )

    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        print(f"access token: {access_token}")
        print(f"refresh token: {refresh_token}")

        if (
            request.path.startswith("/static/") or
            request.path.startswith("/staticfiles/") or
            request.path.startswith("/media/") or
            request.path.startswith("/auth/activate/") or
            request.path in [
                "/", "/auth/logout/" , "/auth/register/",
                "/auth/token/", "/auth/token/refresh/", "/i18n/setlang/" , "/parking/test/","/parking/areas/",
            ]
        ):
            return self.get_response(request)

        if not access_token or not refresh_token:
            print("o tokens in cookies.")
            return self.clear()

        try:
            self.token_backend.decode(refresh_token, verify=True)
        except (InvalidToken, TokenError, Exception) as e:
            print(f"invalid refresh token: {str(e)}")
            return self.clear()

        try:
            return self.get_response(request)
        except (InvalidToken, TokenError) as exc:
            print("invalid access token detected.")
            return self.clear()

    def clear(self):
        response = redirect('/')
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')
        return response
