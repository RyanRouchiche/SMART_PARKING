from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from users.serializers import  GuestSerializer , AdminSerializer , ListUserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import  timedelta
from django.contrib.auth import authenticate , login , logout
from .models import auth
from django.utils.timezone import now
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.contrib.auth.tokens import default_token_generator
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from rest_framework_simplejwt.exceptions import TokenError, InvalidToken
from .permission import IsAdmin
from .models import User
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework_simplejwt.tokens import AccessToken
logger = logging.getLogger(__name__)

from .utils import SETupCOOKIE , send_verif_email
from .models import auth 


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]
    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                logger.error("Username or password not provided")
                return Response({'success': False, 'error': 'Username and password are required'}, status=400)

            user = authenticate(username=username, password=password)
            if not user:
                logger.error("Invalid credentials")
                return Response({'success': False, 'error': 'Invalid credentials'}, status=401)

            if not user.is_active:
                logger.error("User account is inactive")
                return Response({'success': False, 'error': 'Your account is invalid, check your email for validation'}, status=401)

            login(request, user)

            request.session['id'] = str(user.id)
            request.session['username'] = user.username
            request.session['email'] = user.email
            request.session['user_type'] = user.user_type

             
            auth.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

            refresh = RefreshToken.for_user(user)
            logger.info(f"Generated refresh token: {refresh}")
            access_token = str(refresh.access_token)
            logger.info(f"Generated access token: {access_token}")
            refresh_token = str(refresh)

            expires_at = now() + timedelta(hours=1)
            

            auth.objects.update_or_create(
                user=user,
                defaults={
                    'refresh_token': refresh_token,
                    'expires_at': expires_at,
                    'is_revoked': False,
                    'created_at': now()
                }
            )

            user_data = {
                'username': user.username,
                'email': user.email,
                'role': user.user_type,
                'id': str(user.id)
            }

            res = Response({
                'success': True,
                'message': 'Login successful',
                'user': user_data,
                'status': 200
            }, status=status.HTTP_200_OK)
            
            SETupCOOKIE(res, 'access_token', access_token) 
            SETupCOOKIE(res, 'refresh_token', refresh_token)


            return res

        except Exception as e:
            logger.error(f"Error in CustomTokenObtainPairView: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)
        
class CustomObtainRefreshToken(TokenRefreshView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            logger.info(f"Refresh token from cookies: {refresh_token}")

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token not found in cookies'}, status=status.HTTP_401_UNAUTHORIZED)

            try:
                token_obj = auth.objects.get(refresh_token=refresh_token)
                if token_obj.is_revoked:
                    logger.error("Refresh token is revoked")
                    return Response({'success': False, 'error': 'Refresh token is revoked'}, status=status.HTTP_401_UNAUTHORIZED)
            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token not recognized'}, status=status.HTTP_401_UNAUTHORIZED)

            request.data['refresh'] = refresh_token

            try:
                response = super().post(request, *args, **kwargs)
            except TokenError as e:
                logger.warning(f"TokenError in refresh: {str(e)}")
                return Response({'success': False, 'error': 'Token is blacklisted or invalid'}, status=status.HTTP_401_UNAUTHORIZED)
            except InvalidToken as e:
                logger.warning(f"InvalidToken in refresh: {str(e)}")
                return Response({'success': False, 'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

            access_token = response.data.get('access')
            logger.info(f"New access token in class refresh: {access_token}")

            new_refresh_token = response.data.get('refresh')
            logger.info(f"New refresh token in class refresh: {new_refresh_token}")
            
            if not access_token or not new_refresh_token:
                logger.error("Failed to obtain new access token or refresh token")
                logger.error("Failed to obtain new access token")
                return Response({'success': False, 'error': 'Failed to refresh token'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            res = Response({'refresh': True, 'message': 'Access token refreshed successfully' , 'status' : 200}, status=status.HTTP_200_OK)
            SETupCOOKIE(res, 'access_token', access_token)
            SETupCOOKIE(res, 'refresh_token', new_refresh_token)
            try :
                token_obj.refresh_token = new_refresh_token
                token_obj.expires_at = now() + timedelta(hours=1)
                token_obj.save()
            except Exception as e:
                logger.error(f"Error updating token in DB: {str(e)}", exc_info=True)
                return Response({'success': False, 'error': 'Failed to update token in DB'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return res

        except Exception as e:
            logger.error(f"Unexpected error in refresh: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'Unexpected error during refresh'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
      
      
class LogoutView(APIView):
    permission_classes = [AllowAny] 

    def post(self, request, *args, **kwargs):
        try:
           
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token introuvable dans les cookies'}, status=401)

            try:
                
                token_entry = auth.objects.get(refresh_token=refresh_token)

               
                if token_entry.is_revoked:
                    return Response({'success': False, 'error': 'Token déjà révoqué'}, status=400)

                if not token_entry.is_valid():
                    return Response({'success': False, 'error': 'Token expired ou invalide'}, status=401)

                token_entry.is_revoked = True
                token_entry.save()

            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token non found in db'}, status=404)

            response = Response({'success': True, 'message': 'Déconnexion réussie' , 'status' : 200})

            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            SETupCOOKIE(response, 'access_token','')
            SETupCOOKIE(response, 'refresh_token','')
            return response

        except Exception as e:
            logger.error(f"[LOGOUT ERROR] {str(e)}", exc_info=True)
            print("error in logout : ", str(e)) 
            return Response({'success': False, 'error': 'Erreur inattendue lors de la déconnexion'}, status=500)

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

class ActivateUserAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
            logger.info("user",user) 
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account activated successfully!' , 'status' : 200}, status=status.HTTP_200_OK)
        return Response({'error': 'Invalid activation link.'}, status=status.HTTP_400_BAD_REQUEST)
    
class RegisterAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request):
        return render(request, 'register.html')
    def post(self, request):
        serializer = AdminSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            send_verif_email(request , user)
            return Response({'message' : 'user admin register , check your email for account activation' , 'value' : 1 , 'status' : 200}, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GuestViewAPI(APIView) : 
    permission_classes  = [IsAuthenticated , IsAdmin]
    def post(self, request) :
        try : 
            serializer = GuestSerializer(data=request.data ,  context={'request': request})
            if serializer.is_valid() : 
                user = serializer.save()
                send_verif_email(request , user)
                
                return Response({'message': 'Guest successfully check email verify account' , 'value' : 1 , 'status' : 200}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e : 
            logger.error(f"Error in GuestViewAPI: {str(e)}", exc_info=True)
            print("error in guest view api : ", str(e))
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)

class ListUserViewAPI(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]
 

    def get(self, request , *args, **kwargs)  :
        logger.info(f"authenticated user: {request.user}")
        print("authenticated user : ", request.user)
        return render(request, 'liste-user.html')
    def post(self, request , *args, **kwargs)  :
        try:
            users = User.objects.filter(user_type='guest')
            serializer = ListUserSerializer(users, many=True)
            return Response({'success': True, 'users': serializer.data,'value' : 1 , 'status' : 200}, status=200)
           
        except Exception as e:
            logger.error(f"Error in ListUserViewAPI: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred','value' : 0}, status=500)
        

class DeleteeUserViewAPI(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]


    def delete(self,  request, user_id ,  *args, **kwargs):
        try:
   
            logger.info(f"User ID to delete: {user_id}")

            if not user_id:
                return Response({'success': False, 'error': 'User id is required'}, status=400)

            try:
                user_to_delete = User.objects.get(id=user_id)
            except User.DoesNotExist:
                return Response({'success': False, 'error': 'User not found'}, status=404)

            if request.user.user_type != 'admin':
                return Response({'success': False, 'error': 'You do not have permission to delete users'}, status=403)

            auth_records = auth.objects.filter(user=user_to_delete)
            for record in auth_records:
                record.is_revoked = True 
                record.save()

            tokens = OutstandingToken.objects.filter(user=user_to_delete)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            user_to_delete.delete()

            return Response({'success': True, 'message': f'User  {user_to_delete.first_name} {user_to_delete.last_name} has been deleted' , 'status' : 200}, status=200)

        except Exception as e:
            logger.error(f"Error in DeleteeUserViewAPI: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)
        
class LoginView(APIView) : 
    permission_classes = [AllowAny]
    def get(self, request , *args, **kwargs) : 
        return render(request, 'login.html')
    
class check_auth(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user
            logger.info(f"Authenticated user: {user}")
            access_token = request.COOKIES.get('access_token')
            logger.info(f"Access token from cookies: {access_token}")
            if not access_token:
                return Response({'success': False, 'error': 'No access token found', 'status': 401}, status=401)
            try:
                AccessToken(access_token)
            except TokenError as e:
                return Response({'success': False, 'error': 'Access token is expired or invalid', 'status': 401}, status=401)
            if user.is_authenticated:
                return Response({'success': True, 'message': 'User is authenticated', 'status': 200}, status=200)
            else:
                return Response({'success': False, 'error': 'User is not authenticated', 'status': 401}, status=401)
        except Exception as e:
            logger.error(f"Error in check_auth: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)