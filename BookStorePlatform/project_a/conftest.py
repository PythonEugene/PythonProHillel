import pytest
from rest_framework.test import APIClient
from django.core.cache import caches
from users.models import CustomUser
from users.tests.factories import UserFactory
from celery import current_app
from unittest.mock import MagicMock


@pytest.fixture
def user(db):
    return CustomUser.objects.create_user(
        email="u@test.com",
        first_name="Ivan",
        phone_number="+380501111111",
        password="pass12345",
    )


@pytest.fixture
def auth_client(client, user):
    client.force_login(user)
    return client


@pytest.fixture(autouse=True)
def clear_caches():
    """Throttle counters live in the cache; reset them before every test."""
    for alias in caches:
        caches[alias].clear()


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
        email='admin@test.com',
        first_name='Admin',
        phone_number='+380500000099',
        password='pass12345',
    )


@pytest.fixture
def admin_api(admin_user):
    """API client authenticated as an administrator."""
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


@pytest.fixture(autouse=True)
def celery_eager(settings):
    from DjangoBookStore.celery import app
    settings.CELERY_TASK_ALWAYS_EAGER = True
    settings.CELERY_TASK_EAGER_PROPAGATES = True
    app.conf.task_always_eager = True
    app.conf.task_eager_propagates = True

@pytest.fixture(autouse=True)
def mock_warehouse(monkeypatch):
    """Existing tests must not call the real warehouse service."""
    fake = MagicMock()
    monkeypatch.setattr('orders.views.WarehouseClient', lambda: fake)
    monkeypatch.setattr('orders.tasks.WarehouseClient', lambda: fake)
    return fake
