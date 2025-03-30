from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Доступ на чтение для всех, но редактирование только для админов.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and request.user.is_staff