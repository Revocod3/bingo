from rest_framework import permissions

class IsSellerPermission(permissions.BasePermission):
    """
    Permission to check if user is a seller
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.is_seller
        # Assuming you have a custom user model with an is_seller field
