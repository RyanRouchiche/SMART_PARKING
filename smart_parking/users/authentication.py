from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentification(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not access_token:
            return None
        
        validated_token = self.get_validated_token(access_token)
        try : 
            user = self.get_user(validated_token)
        except Exception as e:
            print(e)
            return None
        return (user, validated_token)