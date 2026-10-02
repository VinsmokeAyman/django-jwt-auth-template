from rest_framework.permissions import BasePermission


class IsTier1(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "tier1"
        )


class IsCompanyAdmin(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated
            and request.user.role == "admin"
        )