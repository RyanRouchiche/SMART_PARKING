from django.contrib import admin, messages

from . import services
from .models import OwnerRequest


@admin.register(OwnerRequest)
class OwnerRequestAdmin(admin.ModelAdmin):
    list_display = ('parking_name', 'name', 'phone', 'email', 'status', 'parking', 'created_at')
    list_filter = ('status', 'fiber', 'language')
    search_fields = ('parking_name', 'name', 'email', 'phone', 'address')
    list_editable = ('status',)
    readonly_fields = ('parking',)
    actions = ['accept']

    @admin.action(description="Accepter : créer le parking en brouillon pour le propriétaire")
    def accept(self, request, queryset):
        for owner_request in queryset.filter(parking__isnull=True):
            if services.accept_owner_request(owner_request):
                self.message_user(request, f"« {owner_request.parking_name} » créé pour {owner_request.email}.", messages.SUCCESS)
            else:
                self.message_user(
                    request,
                    f"Aucun compte propriétaire actif avec l'e-mail {owner_request.email}. "
                    "Demandez-lui de créer son compte sur le web pro, puis relancez l'action.",
                    messages.WARNING,
                )
