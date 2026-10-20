from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView, LogoutView
from django.http import HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.urls import reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import FormView, CreateView
from .forms import CustomUserCreationForm, UserPermissionForm

User = get_user_model()


class PermissionManagementService:
    """Business logic for changing the permissions of a user."""

    @staticmethod
    def update_user_permissions(user, permission_ids):
        """Replace all permissions of the user with the selected ones.

        Args:
            user: the user whose permissions are changed.
            permission_ids: ids of the permissions that the user must have.
        """
        user.user_permissions.set(Permission.objects.filter(id__in=permission_ids))


class ManagerUserPermissionsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    """Page for managing the permissions of a user.
    Viewing requires the `can_see_user_permissions` permission, changing
    requires can_set_user_permissions. Users without the first permission
    get 403, users with only the first one see a read-only form.
    """

    template_name = 'permissions_management.html'
    form_class = UserPermissionForm

    def test_func(self):
        """Allow access only to users who may see user permissions."""
        return self.request.user.has_perm('users.can_see_user_permissions')

    def handle_no_permission(self):
        """Return 403 instead of a redirect when access is denied."""
        return HttpResponseForbidden('Have no access to requested page')

    @cached_property
    def target_user(self):
        """The user whose permissions are edited (one query per request).

        Returns 404 if the user does not exist.
        """
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def get_form_kwargs(self):
        """Pass the target user and the current manager to the form."""
        kwargs = super().get_form_kwargs()
        kwargs.update({'user': self.target_user, 'manager': self.request.user})
        return kwargs

    def get_context_data(self, **kwargs):
        """Add target_user to the template context."""
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.target_user
        return context

    def get_success_url(self):
        """Return to the same page after saving."""
        return reverse_lazy('users:manage_permissions', kwargs={'user_id': self.kwargs['user_id']})

    def form_valid(self, form):
        """Save the selected permissions.

        Returns 403 if the manager has no can_set_user_permissions
        permission, even if the request was crafted manually.
        """
        if not self.request.user.has_perm('users.can_set_user_permissions'):
            return HttpResponseForbidden('No permission to change permissions')
        PermissionManagementService.update_user_permissions(
            self.target_user, form.cleaned_data.get('permissions', [])
        )
        return super().form_valid(form)


class RegisterView(CreateView):
    """Registration page.
    On success the user is created and redirected to the login page.
    """

    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')


class CustomLoginView(LoginView):
    """Login page. The username is the phone number."""

    template_name = 'users/login.html'


class CustomLogoutView(LogoutView):
    """Log the user out (POST) and redirect to the book catalog."""

    next_page = reverse_lazy('books:list')
