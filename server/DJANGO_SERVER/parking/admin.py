from django.contrib import admin

from .models import Parking, ParkingMembership, Zone


class MembershipInline(admin.TabularInline):
    model = ParkingMembership
    extra = 0


class ZoneInline(admin.TabularInline):
    model = Zone
    extra = 0
    fields = ('number', 'name', 'camera')


@admin.register(Parking)
class ParkingAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'capacity', 'is_published', 'created_at')
    list_filter = ('is_published',)
    search_fields = ('name', 'address')
    inlines = [ZoneInline, MembershipInline]


@admin.register(Zone)
class ZoneAdmin(admin.ModelAdmin):
    list_display = ('parking', 'number', 'name', 'camera')
    list_filter = ('parking',)
