

from rest_framework_simplejwt.authentication import JWTAuthentication
import logging

logger = logging.getLogger(__name__)

class CookieJWTAuthentification(JWTAuthentication):
    def authenticate(self, request):
        access_token = request.COOKIES.get('access_token')
        refresh_token = request.COOKIES.get('refresh_token')
        
        if not access_token:
            return None
        
        try:
            validated_token = self.get_validated_token(access_token)
            
            user = self.get_user(validated_token)
        except Exception as e:
            logger.error(f"Error in user authentication: {str(e)}")
            return None
        
        return (user, validated_token)
