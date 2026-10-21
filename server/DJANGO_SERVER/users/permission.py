from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdmin(BasePermission):
    message = "admin only"

    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type.lower() == 'admin'


class IsAdminOrReadOnly(IsAdmin):
    def has_permission(self, request, view):
        return request.method in SAFE_METHODS or super().has_permission(request, view)
