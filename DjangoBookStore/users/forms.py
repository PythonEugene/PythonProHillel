from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import Permission
from .models import CustomUser

User  = get_user_model()


class UserPermissionForm(forms.Form):
     readonly_fields_if_no_manage_perm = [
         'permissions'
     ]

     permissions = forms.MultipleChoiceField(
         widget=forms.CheckboxSelectMultiple,
         required=False,
     )

     def __init__(self, *args, user=None, manager=None, **kwargs):
         super().__init__(*args, **kwargs)
         self.user = user
         self.manager = manager
         permissions = Permission.objects.all()
         self.fields['permissions'].choices = [
             (perm.id, f'{perm.content_type.app_label}.{perm.codename} - {perm.name}')
             for perm in permissions.order_by('content_type__app_label', 'codename')
         ]
         can_manage = self.manager.has_perm('users.can_set_user_permissions') if self.manager else False
         if self.user:
             user_permissions = self.user.user_permissions.values_list('id', flat=True)
             self.fields['permissions'].initial = list(user_permissions)
         if not can_manage:
             self._read_only_view()

         def _read_only_view(self):
             for field in self.readonly_fields_if_no_manage_perm:
                 self.fields[field].disabled = True


class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'phone_number', 'first_name', 'last_name')


