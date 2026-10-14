import pytest
from django.db import IntegrityError
from users.models import CustomUser


@pytest.mark.django_db
def test_create_user(user):
    assert user.check_password("pass12345")
    assert not user.is_staff and user.is_active


@pytest.mark.django_db
def test_create_user_without_phone_raises():
    with pytest.raises(ValueError):
        CustomUser.objects.create_user(email="a@a.com", first_name="A", phone_number="")


@pytest.mark.django_db
def test_create_user_without_email_raises():
    with pytest.raises(ValueError):
        CustomUser.objects.create_user(email="", first_name="A", phone_number="+380500000001")


@pytest.mark.django_db
def test_create_superuser_flags():
    su = CustomUser.objects.create_superuser(
        email="s@s.com", first_name="S", phone_number="+380500000002", password="x12345678")
    assert su.is_staff and su.is_superuser


@pytest.mark.django_db
def test_user_str(user):
    assert str(user) == "u@test.com"


@pytest.mark.django_db
def test_phone_number_unique(user):
    with pytest.raises(IntegrityError):
        CustomUser.objects.create_user(
            email="other@test.com", first_name="B", phone_number=user.phone_number)