from functools import lru_cache
from rest_framework.permissions import BasePermission


class DenyAll(BasePermission):
    """Used for actions that are not listed in permission_by_action."""

    def has_permission(self, request, view):
        return False


@lru_cache(maxsize=None)
def require_perm(codename):
    """Return a permission class that requires the permission stock.<codename>."""

    class RequiresPermission(BasePermission):
        message = f'Permission "{codename}" is required.'

        def has_permission(self, request, view):
            user = request.user
            return bool(user and user.is_authenticated and user.has_perm(f'stock.{codename}'))

    RequiresPermission.__name__ = f'Requires_{codename}'
    return RequiresPermission


class ActionPermissionMixin:
    """Choose the required permission by the name of the current action.
    A view sets `permission_by_action = {'list': 'view_stockitem', ...}`.
    Actions that are not listed are denied.
    """

    permission_by_action = {}

    def get_permissions(self):
        codename = self.permission_by_action.get(self.action)
        if codename is None:
            return [DenyAll()]
        return [require_perm(codename)()]
