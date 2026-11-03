from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView

from parking.interface import get_parking, owned_parkings, zone_layouts
from . import services
from .models import Camera
from .serializers import MAX_AREAS, AreaSerializer, CameraSerializer


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
        if not services.delete_camera(camera_id, owned_parkings(request.user)):
            return Response({'error': 'Camera not found'}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['GET'])
def snapshots(request):
    parking = get_parking(request, owner=True)
    return Response({'images': services.snapshots(parking.id)})


@api_view(['GET', 'POST'])
def coordinates(request):
    if request.method == 'GET':
        return Response({'data': zone_layouts(get_parking(request))})

    parking = get_parking(request, owner=True)
    serializer = AreaSerializer(data=request.data, many=True, max_length=MAX_AREAS)
    serializer.is_valid(raise_exception=True)
    services.save_layout(parking, serializer.validated_data)
    return Response({'message': 'Coordinates saved'}, status=status.HTTP_201_CREATED)
