from django.contrib import admin

from .models import OwnerRequest


@admin.register(OwnerRequest)
class OwnerRequestAdmin(admin.ModelAdmin):
    list_display = ('parking_name', 'name', 'phone', 'email', 'status', 'created_at')
    list_filter = ('status', 'fiber', 'language')
    search_fields = ('parking_name', 'name', 'email', 'phone', 'address')
    list_editable = ('status',)
