from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission for Admin users only.
    Admins can:
    - View all clients
    - Assign clients to CSMs
    - View all CSM users
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.user.role and request.user.role.name.lower() == 'admin':
            return True
        return False


class IsCSM(permissions.BasePermission):
    """
    Permission for CSM (Customer Success Manager) users.
    CSMs can:
    - View their assigned clients only
    - Update client stages
    - View client context/details
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.role and request.user.role.name.lower() == 'csm':
            return True
        return False


class IsAdminOrCSM(permissions.BasePermission):
    """
    Permission for both Admin and CSM users.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser:
            return True
        if request.user.role:
            role_name = request.user.role.name.lower()
            if role_name in ['admin', 'csm']:
                return True
        return False
