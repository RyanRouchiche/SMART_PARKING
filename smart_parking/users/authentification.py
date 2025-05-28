

from rest_framework_simplejwt.authentication import JWTAuthentication
import logging
from rest_framework.exceptions import AuthenticationFailed
logger = logging.getLogger(__name__)

class CookieJWTAuthentification(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        logger.info(f"Access token from cookies: {access_token}")
        if not access_token  : 
            logger.info("No access token found in cookies")
           
            return None
        validated_token = self.get_validated_token(access_token)
        logger.info(f"Validated token: {validated_token}")
        try : 
            user = self.get_user(validated_token)
            logger.info(f"Authenticated user: {user}")
        except Exception as e:
            logger.error(f"Error in JWT authentication: {e}")
            raise  AuthenticationFailed("Invalid token")
            return None
        return (user, validated_token)
