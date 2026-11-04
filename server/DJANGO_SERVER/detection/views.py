from django.contrib import admin
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from parking.interface import get_parking
from .health import report
from .stats import MAX_DAYS, hourly_occupancy


def supervision(request):
    context = {**admin.site.each_context(request), 'title': "Supervision", 'report': report()}
    return render(request, 'admin/supervision.html', context)


class StatsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        parking = get_parking(request, owner=True)
        try:
            days = int(request.query_params.get('days', MAX_DAYS))
        except ValueError:
            return Response({'error': 'days must be a number'}, status=400)
        days = min(max(days, 1), MAX_DAYS)
        return Response({'days': days, 'hours': hourly_occupancy(parking.pk, days)})
