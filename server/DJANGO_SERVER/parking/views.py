from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from camera.services import snapshots as camera_snapshots
from . import services
from .access import get_parking
from .serializers import AreaSerializer, MAX_AREAS


@api_view(['GET'])
def snapshots(request):
    parking = get_parking(request, owner=True)
    return Response({'images': camera_snapshots(parking.id)})


@api_view(['GET', 'POST'])
def coordinates(request):
    if request.method == 'GET':
        return Response({'data': services.zone_layouts(get_parking(request))})

    parking = get_parking(request, owner=True)
    serializer = AreaSerializer(data=request.data, many=True, max_length=MAX_AREAS)
    serializer.is_valid(raise_exception=True)
    services.save_zones(parking, serializer.validated_data)
    return Response({'message': 'Coordinates saved'}, status=status.HTTP_201_CREATED)


@api_view(['GET'])
def areas(request):
    return Response({'areas': services.zone_numbers(get_parking(request))})
