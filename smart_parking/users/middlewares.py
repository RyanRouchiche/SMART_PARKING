from django.shortcuts import redirect
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError

class InvalidJWTMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        access_token = request.COOKIES.get('access_token')
        print(f"Access token from cookies middle: {access_token}")

        if (
            request.path.startswith("/static/") or
            request.path.startswith("/staticfiles/") or
            request.path.startswith("/media/") or
            request.path in ["/logout/", "/login/", "/register/", "/" , "/auth/token/" , "/auth/token/refresh/","/i18n/setlang/"] 
        ):
            return self.get_response(request)

        if not access_token:
            print("No access token found in cookies")
            response = redirect('/')
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        try:
            return self.get_response(request)
        except (InvalidToken, TokenError) as exc:
            print("InvalidJWTMiddleware triggered in __call__!")
            response = redirect('/')
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            return response
        
