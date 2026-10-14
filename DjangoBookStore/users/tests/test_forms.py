import pytest
from django.contrib.auth.models import Permission
from users.forms import CustomUserCreationForm, UserPermissionForm

VALID = {
    "email": "new@test.com", "phone_number": "+380502222222",
    "first_name": "Ivan", "last_name": "P",
    "password1": "Str0ngPass!234", "password2": "Str0ngPass!234",
}


@pytest.mark.django_db
def test_creation_form_valid():
    assert CustomUserCreationForm(data=VALID).is_valid()


@pytest.mark.django_db
def test_creation_form_password_mismatch():
    form = CustomUserCreationForm(data={**VALID, "password2": "other"})
    assert not form.is_valid()
    assert "password2" in form.errors


@pytest.mark.django_db
def test_creation_form_duplicate_email(user):
    form = CustomUserCreationForm(data={**VALID, "email": user.email})
    assert not form.is_valid()
    assert "email" in form.errors


@pytest.mark.django_db
def test_permission_form_readonly_without_perm(user):
    form = UserPermissionForm(user=user, manager=user)
    assert form.fields["permissions"].disabled is True


@pytest.mark.django_db
def test_permission_form_editable_with_perm(user):
    manager = user
    perm = Permission.objects.get(codename="can_set_user_permissions")
    manager.user_permissions.add(perm)
    manager = type(manager).objects.get(pk=manager.pk)  # сбросить кеш прав
    form = UserPermissionForm(user=None, manager=manager)
    assert form.fields["permissions"].disabled is False