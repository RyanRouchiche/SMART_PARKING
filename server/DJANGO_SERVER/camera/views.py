from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from parking.access import get_parking, member_parkings
from parking.models import ParkingMembership
from . import services
from .models import Camera
from .serializers import CameraSerializer


def camera_list(cameras):
    cameras = list(cameras)
    health = services.camera_health(c.path for c in cameras)
    return CameraSerializer(cameras, many=True, context={'health': health}).data


class CameraListView(APIView):
    def get(self, request):
        parking = get_parking(request, owner=True)
        return Response({'cameras': camera_list(Camera.objects.filter(parking=parking))})

    def post(self, request):
        parking = get_parking(request, owner=True)
        serializer = CameraSerializer(data=request.data, many=True, context={'parking': parking})
        serializer.is_valid(raise_exception=True)
        cameras = services.add_cameras(parking, serializer.validated_data)
        return Response({'cameras': camera_list(cameras)}, status=status.HTTP_201_CREATED)


class CameraDetailView(APIView):
    def delete(self, request, camera_id):
        if not services.delete_camera(camera_id, member_parkings(request.user, ParkingMembership.OWNER)):
            return Response({'error': 'Camera not found'}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)
