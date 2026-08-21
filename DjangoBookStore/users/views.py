from django.shortcuts import render, get_object_or_404
from django.http.response import HttpResponse
from typing import Any
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.models import Permission
from django.contrib.auth.views import LoginView, LogoutView
from .forms import UserPermissionForm
from django.views.generic import FormView, CreateView
from django.http import HttpResponseForbidden
from django.urls import reverse_lazy
from .forms import CustomUserCreationForm

User = get_user_model()

class PermissionManagementService:
    @staticmethod
    def update_user_permissions(user, permission_ids):
        user.user_permissions.clear()
        permissions = Permission.objects.filter(id__in=permission_ids)
        user.user_permissions.set(permissions)

class ManagerUserPermissionsView(LoginRequiredMixin, UserPassesTestMixin, FormView):
    template_name = 'permissions_management.html'
    form_class = UserPermissionForm

    def test_func(self) -> bool | None:
        return self.request.user.has_perm('users.can_see_user_permissions')

    def handle_no_permission(self):
        return HttpResponseForbidden('Have no access to requested page')

    def get_target_user(self):
        return get_object_or_404(User, id=self.kwargs['user_id'])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'user': self.get_target_user(),
            'manager': self.request.user
        })
        return kwargs

    def get_context_data(self, **kwargs: Any):
        context = super().get_context_data(**kwargs)
        context['target_user'] = self.get_target_user()
        return context

    def get_success_url(self) -> str:
        return reverse_lazy('manage_permissions', kwargs={'user_id': self.kwargs['user_id']})

    def form_valid(self, form: Any):
        selected_permissions = form.cleaned_data.get('permissions', [])
        target_user = self.get_target_user()

        PermissionManagementService.update_user_permissions(
            target_user,
            selected_permissions
        )
        return super().form_valid(form)


class RegisterView(CreateView):
    form_class = CustomUserCreationForm
    template_name = 'users/register.html'
    success_url = reverse_lazy('users:login')\


class CustomLoginView(LoginView):
    template_name = 'users/login.html'


class CustomLogoutView(LogoutView):
    next_page = reverse_lazy('books:list')

