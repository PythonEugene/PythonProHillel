import pytest
from users.models import CustomUser
from django.core.cache import cache
from rest_framework.test import APIClient

from users.models import CustomUser
from users.tests.factories import UserFactory


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email="u@test.com", first_name="Ivan",
        phone_number="+380501111111", password="pass12345",
    )
@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture(autouse=True)
def clear_throttle_cache():
    """Throttle counters live in the cache; reset them before every test."""
    cache.clear()


@pytest.fixture
def api_client():
    """Anonymous API client."""
    return APIClient()


@pytest.fixture
def user_api(user):
    """API client authenticated as a regular user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def other_user(db):
    return UserFactory()


@pytest.fixture
def admin_user(db):
    return CustomUser.objects.create_superuser(
        email='admin@test.com', first_name='Admin',
        phone_number='+380500000099', password='pass12345')


@pytest.fixture
def admin_api(admin_user):
    """API client authenticated as an administrator."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client