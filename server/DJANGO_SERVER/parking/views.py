from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.interface import AccountSerializer, OperatorAccountSerializer, accounts_with_status
from . import services
from .access import get_parking, owned_parkings


@api_view(['GET'])
def areas(request):
    return Response({'areas': services.zone_numbers(get_parking(request))})


class OperatorListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        parking = get_parking(request, owner=True)
        operators = accounts_with_status(services.operator_ids(parking))
        return Response({'users': AccountSerializer(operators, many=True).data})

    def post(self, request):
        parking = get_parking(request, owner=True)
        serializer = OperatorAccountSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        services.add_operator(serializer, parking, request)
        return Response({'message': 'Guest created, activation email sent'}, status=status.HTTP_201_CREATED)


class OperatorDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, user_id):
        if not services.remove_operator(user_id, owned_parkings(request.user)):
            return Response({'error': 'User not found'}, status=404)
        return Response(status=status.HTTP_204_NO_CONTENT)
