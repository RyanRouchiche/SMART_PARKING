from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permission import IsAdmin
from .models import Camera
from .serializers import CameraSerializer


class CameraListView(APIView):
    permission_classes = [IsAdmin]

    def get(self, request):
        return Response({'cameras': CameraSerializer(Camera.objects.all(), many=True).data})

    def post(self, request):
        serializer = CameraSerializer(data=request.data, many=True)
        serializer.is_valid(raise_exception=True)
        cameras = Camera.objects.bulk_create([Camera(**data) for data in serializer.validated_data])
        return Response({'cameras': CameraSerializer(cameras, many=True).data}, status=status.HTTP_201_CREATED)


class CameraDetailView(APIView):
    permission_classes = [IsAdmin]

    def delete(self, request, camera_id):
        deleted, _ = Camera.objects.filter(id=camera_id).delete()
        if not deleted:
            return Response({'error': 'Camera not found'}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)
