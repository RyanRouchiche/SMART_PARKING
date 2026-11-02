from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from parking.access import get_parking, member_parkings
from parking.models import ParkingMembership
from .models import Camera
from .serializers import CameraSerializer


class CameraListView(APIView):
    def get(self, request):
        parking = get_parking(request, owner=True)
        return Response({'cameras': CameraSerializer(Camera.objects.filter(parking=parking), many=True).data})

    def post(self, request):
        parking = get_parking(request, owner=True)
        serializer = CameraSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        cameras = Camera.objects.bulk_create([Camera(parking=parking, **data) for data in serializer.validated_data])
        return Response({'cameras': CameraSerializer(cameras, many=True).data}, status=status.HTTP_201_CREATED)


class CameraDetailView(APIView):
    def delete(self, request, camera_id):
        owned = member_parkings(request.user, ParkingMembership.OWNER)
        deleted, _ = Camera.objects.filter(id=camera_id, parking__in=owned).delete()
        if not deleted:
            return Response({'error': 'Camera not found'}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)
