from rest_framework.permissions import BasePermission
class IsAdmin(BasePermission):
    message = "admin only"
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_type == 'admin' or request.user.user_type == 'Admin'