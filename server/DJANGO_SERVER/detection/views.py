from django.contrib import admin
from django.shortcuts import render

from .health import report


def supervision(request):
    context = {**admin.site.each_context(request), 'title': "Supervision", 'report': report()}
    return render(request, 'admin/supervision.html', context)
