from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework.permissions import AllowAny , IsAuthenticated
from .serializers import CameraSerializer
from .models import Camera
import uuid
from uuid import UUID

from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render
from .serializers import CameraSerializer
from users.permission import IsAdmin
import logging
logger = logging.getLogger(__name__)

class ConfigViewAPI(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]
    def get(self, request, *args, **kwargs):
        logger.info("user :  %s " , request.user)
        return render(request, 'cameraconfig.html')

    def post(self, request, *args, **kwargs):
        camera_objects = []
        errors = []

        for data in request.data:
            serializer = CameraSerializer(data=data)
            if serializer.is_valid():
                camera = Camera(**serializer.validated_data)
                camera_objects.append(camera)
            else:
                errors.append(serializer.errors)

        if camera_objects:
            Camera.objects.bulk_create(camera_objects)  
            serialized_data = CameraSerializer(camera_objects, many=True).data
            return Response({
                "success": True,
                "message": "Cameras saved successfully",
                "data": serialized_data , 
                "status" : 200
            }, status=201)
        else:
            return Response({
                "success": False,
                "message": "Cameras not saved",
                "errors": errors
            }, status=400)


class CameraListAPI(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]
    def get(self, request , *args, **kwargs):
        return render(request, 'camera-liste.html')
    
    def post(self, request , *args, **kwargs):
        cameras = Camera.objects.all()
        serializer = CameraSerializer(cameras , many=True)
        
        return Response({"success" : True,"message" : "cam list", "cameras" : serializer.data  , 'status' : 200}, status=200)


    
class CameraDeleteViewAPI(APIView):
    permission_classes = [IsAuthenticated , IsAdmin]
    def delete(self, request , uuid  , *args, **kwargs):
        logger.info("user :  %s " , request.user)
    
        if request.user.user_type != 'admin':
            return Response({'success': False, 'error': 'You do not have permission to delete users'}, status=403)
        
        camera = Camera.objects.get(id=uuid)
        
        if camera is None:
            return Response({"success" : False,"message" : "cam not found"}, status=404)
        camera.delete()
        return Response({"success" : True,"message" : "cam deleted" , "status" : 200}, status=200)