from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.decorators import api_view
from users.serializers import AdminSerializer, GuestSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import permission_classes
from datetime import datetime, timedelta
from django.contrib.auth import authenticate , login , logout
import pytz
from .models import auth
from django.utils.timezone import now
import logging
from rest_framework_simplejwt.tokens import RefreshToken


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

            # Check if the user already has a record in the 'auth' table, and update if exists
            token_entry, created = auth.objects.get_or_create(user=user)
            
            if not created:  # If the record exists, update it
                token_entry.refresh_token = refresh_token
                token_entry.expires_at = expires_at
                token_entry.is_revoked = False  # Make sure the token is not revoked
                token_entry.save()  # Save the updated record
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

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'POST':
        try:
            serializer = AdminSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'message': 'User registered successfully'}, status=201)
            else:
                return Response({'success': False, 'error': serializer.errors}, status=400)
        except Exception as e:
            logger.error(f"Error in register: {str(e)}")
            return Response({'success': False, 'error': str(e)}, status=400)



class loginviewAPI(APIView):
    permission_classes = [AllowAny]
    def get(self, request, *args, **kwargs):
        return render(request, 'login.html')
    
    def post(self, request, *args, **kwargs):
        try:
            response = CustomTokenObtainPairView.as_view()(request._request)

            # Check if the response contains the required data
            if response.status_code == 200:
                tokens = response.data
                access_token = tokens.get('access')
                refresh_token = tokens.get('refresh')

                if access_token and refresh_token:
                 
                    user_info = tokens.get('user', {})
                    user_data = {
                        'username': user_info.get('username'),
                        'email': user_info.get('email'),
                        'user_type': user_info.get('role'),
                        'id': user_info.get('id'),
                    }

                    # Prepare the response
                    res = Response({
                        'success': True,
                        'message': 'Login successful',
                        'user': user_data,
                        'value' : 1
                        
                    })

                    # Set cookies
                    SETupCOOKIE(res, 'access_token', access_token, max_age=10 * 60)
                    SETupCOOKIE(res, 'refresh_token', refresh_token, max_age=30 * 60)

                    return res
                else:
                    return Response({'success': False, 'error': 'Token generation failed.'}, status=400)
            else:
                return response  # Return the raw response (may contain a JSON error)
        except Exception as e:
            logger.error(f"Error in loginviewAPI: {str(e)}", exc_info=True)
            return Response({'success': False, 'error': 'An unexpected error occurred. Please try again later.'}, status=500)


   




    



        

