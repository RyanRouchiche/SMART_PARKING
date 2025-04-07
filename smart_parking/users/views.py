from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.decorators import api_view
from users.serializers import AdminSerializer , GuestSerializer
from rest_framework.permissions import IsAuthenticated , AllowAny
from rest_framework.decorators import permission_classes
from datetime import datetime, timedelta
from django.contrib.auth import authenticate
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
import pytz
from .models import   auth
from django.utils.timezone import now



def SETupCOOKIE(response, key, value, max_age):
    # Get current time in CET (Central European Time)
    local_tz = pytz.timezone('Africa/Algiers')  # Use 'Africa/Cairo' or 'Africa/Algiers'
    local_time = datetime.now(local_tz)  # Current time in CET (GMT+1)

    # Calculate the expiration time in local time (CET/CEST)
    expires_local = local_time + timedelta(seconds=max_age)

    # Convert the local time to UTC
    expires_utc = expires_local.astimezone(pytz.utc)

    # Format the expiration in UTC (GMT)
    response.set_cookie(
        key=key,
        value=value,
        httponly=True,
        secure=True,
        samesite='None',
        path='/',
        max_age=max_age,
        expires=expires_utc.strftime("%a, %d-%b-%Y %H:%M:%S GMT")  # In UTC (GMT)
    )



"""
this class is responsible for creating the token and sending it to the client
and also setting the token in the cookies
and make sure the user login with the username and password return 0 for fail 1 for success
"""
class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        try:
            username= request.data.get('username')
            password= request.data.get('password')
            
            if not username or not password:
                return Response({'success': False, 'error': 'Username and password are required'}, status=400)
            
            
            user = authenticate(username=username, password=password)
            if not user:
                return Response({'success': False, 'error': 'Invalid credentials' , 'value' : 0}, status=401)
            
            # Get tokens using the default logic
            response = super().post(request, *args, **kwargs)
            tokens = response.data
            access_token = tokens.get('access')
            refresh_token = tokens.get('refresh')

            if not access_token or not refresh_token:
                return Response({'success': False, 'error': 'Token generation failed.'}, status=400)
            
            expires_at = now() + timedelta(seconds=30*60)  # 30 minutes from now
            auth.objects.create(
                user=user,
                refresh_token=refresh_token,
                expires_at=expires_at
            )
            
            # Prepare response
            res = Response({'success': True, 'message': 'Login sucess' })

            # Set cookies (10 min access, 30min refresh)
            SETupCOOKIE(res, 'access_token', access_token, max_age=10*60)
            SETupCOOKIE(res, 'refresh_token', refresh_token, max_age=30*60)

            return res
        except Exception as e:
            #print the error
            return Response({'success': False, 'error': str(e)}, status=400)
        
        


""""this class is responsible for refreshing the token and sending it to the client
and also setting the token in the cookies"""
    
class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token not found in cookies'}, status=401)
            
            
            try : 
                token_obj = auth.objects.get(refresh_token=refresh_token)
                if token_obj.is_valid() : 
                    return Response({'success': False, 'error': 'Refresh token is expired'}, status=401)
            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token not found'}, status=401)
            except Exception as e:
                return Response({'success': False, 'error': str(e)}, status=400)

            request.data['refresh'] = refresh_token

            # Get new tokens
            response = super().post(request, *args, **kwargs)
            tokens = response.data
            access_token = tokens.get('access')

            if not access_token:
                return Response({'success': False, 'error': 'Failed to generate access token'}, status=400)

            # Prepare response
            res = Response({'refresh': True, 'message': 'Access token refreshed successfully'})

            # Set new access token in cookie
            SETupCOOKIE(res, 'access_token', access_token, max_age=10*60)

            return res

        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

                
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def getInfoUsers(request) : 
    pass


@api_view(['POST'])
def logout(request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')

            if not refresh_token:
                return Response({'success': False, 'error': 'Refresh token not found in cookies'}, status=401)

            # Revoke the refresh token
            try:
                token_entry = auth.objects.get(token=refresh_token, user=request.user)
                token_entry.is_revoked = True
                token_entry.save()
            except auth.DoesNotExist:
                return Response({'success': False, 'error': 'Refresh token not found in database'}, status=404)

            # Delete cookies
            response = Response({'success': True, 'message': 'Logout successful'})
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')

            return response
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

    

@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    if request.method == 'GET':
        return render(request, 'register.html')
    if request.method == 'POST':
        try:
            serializer = AdminSerializer(data=request.data)
            if serializer.is_valid():
                serializer.save()
                return Response({'success': True, 'message': 'User registered successfully'}, status=201)
            else:
                return Response({'success': False, 'error': serializer.errors}, status=400)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)
        
        
@api_view(['GET', 'POST'])
@permission_classes([AllowAny])
def loginviewAPI(request):
    if request.method == 'GET':
        # Render the login form
        return render(request, 'login.html')

    if request.method == 'POST':
        try:
            # Delegate token generation to CustomTokenObtainPairView
            response = CustomTokenObtainPairView.as_view()(request._request)
            if response.status_code == 200:
                tokens = response.data
                access_token = tokens.get('access')
                refresh_token = tokens.get('refresh')

                # Prepare response
                res = Response({'success': True, 'message': 'Login successful'})

                # Set cookies (10 min access, 30 min refresh)
                SETupCOOKIE(res, 'access_token', access_token, max_age=10 * 60)
                SETupCOOKIE(res, 'refresh_token', refresh_token, max_age=30 * 60)

                return res
            else:
                return response
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashbordviewAPI(request):
    return Response({'success': True, 'message': 'Welcome to the dashboard!'})



    




    



        

