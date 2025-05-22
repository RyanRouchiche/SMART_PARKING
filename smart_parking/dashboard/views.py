from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


import logging
logger = logging.getLogger(__name__)

class DashbordviewAPI(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs) : 
        print(f"Authenticated user: {request.user}")
        return render(request, 'dashboard.html')

    # Handle POST request to send user data
    def post(self, request, *args, **kwargs):
        try:
            # Assuming user data is stored in the session
            username = request.session.get('username')
            id = request.session.get('id')
            role = request.session.get('user_type')
            email = request.session.get('email')

            if username and id and role and email:
                # Return the user data as JSON
                return Response({
                    'success': True,
                    'user': {
                        'username': username,
                        'id': str(id),
                        'role': role,
                        'email': email
                    }
                })
            else:
                return Response({'success': False, 'error': 'User not authenticated'}, status=401)
        except Exception as e:
            print(e)
            return Response({'success': False, 'error': 'An error occurred while fetching user data'}, status=500)

class FormsAPI(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, *args, **kwargs) : 
        print(f"Authenticated user: {request.user}")
        return render(request, 'forms.html')


