from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from users.serializers import  GuestSerializer , AdminSerializer , ListUserSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from datetime import datetime, timedelta
from django.contrib.auth import authenticate , login , logout
import pytz
from .models import auth
from django.utils.timezone import now
import logging
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.encoding import force_str
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.core.mail import EmailMessage

from .models import User


logger = logging.getLogger(__name__)

def SETupCOOKIE(response, key, value, max_age):
    local_tz = pytz.timezone('Africa/Algiers')  
    local_time = datetime.now(local_tz)  
    expires_local = local_time + timedelta(seconds=max_age)
    expires_utc = expires_local.astimezone(pytz.utc)

    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=True,
        samesite='None',
        path='/',
        max_age=max_age,
        expires=expires_utc.strftime("%a, %d-%b-%Y %H:%M:%S GMT")  
    )
    
    
def send_verif_email(request , user) : 
            current_site = get_current_site(request)
            uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            activation_link = f"http://{current_site.domain}/api/activate/{uid}/{token}/"

      
            subject = 'Activate Your Account'
            email_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>Verify Your Email</title>
            </head>
            <body>
                <p>Hi {user.first_name},</p>
                <p>Thank you for registering with Smart Parking. Please click the link below to verify your email address:</p>
                <p>
                    <a href="{activation_link}">Verify Email</a>
                </p>
                <p>If you did not register for this account, please ignore this email.</p>
                <p>Thank you,<br>Smart Parking Team</p>
            </body>
            </html>
            """

            # Send email
            email = EmailMessage(subject, email_body, to=[user.email])
            email.content_subtype = 'html' 
            email.send()
            return Response({'message': 'User registered successfully. Please check your email to verify your account.' , 'value' : 1}, status=status.HTTP_201_CREATED)



class CustomTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, *args, **kwargs):
        return render(request, 'login.html')

    def post(self, request, *args, **kwargs):
        try:
            username = request.data.get('username')
            password = request.data.get('password')

            if not username or not password:
                return Response({'success': False, 'error': 'Username and password are required'}, status=400)

            user = authenticate(username=username, password=password)
            if not user:
                return Response({'success': False, 'error': 'Invalid credentials'}, status=401)
            if not user.is_active  : 
                 return Response({'success': False, 'error': 'your accound is invalid , check your email for validation'}, status=401)
             
            login(request, user)  
            request.session['id'] = str(user.id)
            request.session['username'] = user.username
            request.session['email'] = user.email
            request.session['user_type'] = user.user_type

            # Revoke previous refresh tokens (this will mark old refresh tokens as revoked)
            auth.objects.filter(user=user, is_revoked=False).update(is_revoked=True)

            # Create new tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)

            # Set expiry times
            expires_at = now() + timedelta(seconds=30 * 60)  # 30 minutes for refresh token
            access_token_expiry = now() + timedelta(minutes=5)  # 5 minutes for access token

            
            token_entry, created = auth.objects.get_or_create(user=user, defaults={
                'refresh_token': refresh_token,
                'expires_at': expires_at,
                'is_revoked': False,
                'created_at': now()
            })

            if not created:
                token_entry.refresh_token = refresh_token
                token_entry.expires_at = expires_at
                token_entry.is_revoked = False
                token_entry.created_at = now()
                token_entry.save()

            else:  # If the record doesn't exist, create it
                auth.objects.create(user=user, refresh_token=refresh_token, expires_at=expires_at)

            # Prepare user data to return
            user_data = {
                'username': user.username,
                'email': user.email,
                'role': user.user_type,
                'id': str(user.id)
            }

            # Prepare the success response
            res = Response({
                'success': True,
                'message': 'Login successful',
                'user': user_data,
                'status': 200
            })

            # Set cookies with the access token and refresh token
            res.set_cookie('access_token', access_token, max_age=5 * 60, httponly=True, secure=False, samesite='Lax')  # 5 minutes
            res.set_cookie('refresh_token', refresh_token, max_age=30 * 60, httponly=True, secure=False, samesite='Lax')  # 30 minutes

            return res

        except Exception as e:
            logger.error(f"Error in CustomTokenObtainPairView: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)


class CustomTokenRefreshView(APIView):
    permission_classes = [IsAuthenticated]  
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token not found in cookies'}, status=401)

            try:
                token_obj = auth.objects.get(refresh_token=refresh_token)
                if token_obj.is_revoked or not token_obj.is_valid():
                    return Response({'success': False, 'error': 'Refresh token is invalid or expired'}, status=401)
            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token not found'}, status=401)

            request.data['refresh'] = refresh_token

            # Get new tokens
            response = super().post(request, *args, **kwargs)
            if not hasattr(response, 'data') or 'access' not in response.data:
                return Response({'success': False, 'error': 'Failed to generate access token'}, status=400)

            access_token = response.data['access']

            # Prepare response
            res = Response({'refresh': True, 'message': 'Access token refreshed successfully'})

            # Set new access token in cookie
            SETupCOOKIE(res, 'access_token', access_token, max_age=10 * 60)

            return res
        except Exception as e:
            logger.error(f"Error in CustomTokenRefreshView: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, *args, **kwargs):
        try:
            # Retrieve refresh token from cookies
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token not found in cookies'}, status=401)

            try:
                # Find the token entry in the database
                token_entry = auth.objects.get(refresh_token=refresh_token, user=request.user)

                # If token is already revoked, return an error
                if token_entry.is_revoked:
                    return Response({'success': False, 'error': 'Token is already revoked'}, status=400)

                # Mark the token as revoked
                token_entry.is_revoked = True
                token_entry.save()

            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token not found in database'}, status=404)

            # Prepare the response and delete cookies
            response = Response({'success': True, 'message': 'Logout successful'})

            # Delete cookies by setting their expiration date in the past
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')

            response.set_cookie('access_token', '', expires='Thu, 01 Jan 1970 00:00:00 GMT', httponly=True, secure=True, samesite='Lax')
            response.set_cookie('refresh_token', '', expires='Thu, 01 Jan 1970 00:00:00 GMT', httponly=True, secure=True, samesite='Lax')

            return response
        except Exception as e:
            logger.error(f"Error in logout: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)

class ActivateUserAPIView(APIView):
    permission_classes = [AllowAny]
    def get(self, request, uidb64, token):
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and default_token_generator.check_token(user, token):
            user.is_active = True
            user.save()
            return Response({'message': 'Account activated successfully!'}, status=status.HTTP_200_OK)
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
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    

class GuestViewAPI(APIView) : 
    permission_classes  = [IsAuthenticated]
    def get(self, request) : 
        return render(request, 'guest.html')
    def post(self, request) :
        try : 
            serializer = GuestSerializer(data=request.data ,  context={'request': request})
            if serializer.is_valid() : 
                user = serializer.save()
                send_verif_email(request , user)
                
                return Response({'message': 'Guest   successfully.' , 'value' : 1}, status=status.HTTP_201_CREATED)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e : 
            logger.error(f"Error in GuestViewAPI: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred'}, status=500)

class ListUserViewAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request , *args, **kwargs)  :
        return render(request, 'liste-user.html')
    def post(self, request , *args, **kwargs)  :
        try:
            users = User.objects.filter(user_type='guest')
            serializer = ListUserSerializer(users, many=True)
            return Response({'success': True, 'users': serializer.data,'value' : 1}, status=200)
           
        except Exception as e:
            logger.error(f"Error in ListUserViewAPI: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred','value' : 0}, status=500)

