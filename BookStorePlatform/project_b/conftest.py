import pytest
from django.contrib.auth.models import Group
from django.core.cache import caches
from rest_framework.test import APIClient

from users.models import CustomUser


@pytest.fixture(autouse=True)
def clear_caches():
    """Reset every cache (throttling counters, cached data) before each test."""
    for alias in caches:
        caches[alias].clear()


@pytest.fixture(autouse=True)
def celery_eager():
    """Run Celery tasks synchronously in tests."""
    from warehouse.celery import app

    app.conf.task_always_eager = True


def make_user(email, phone, group=None):
    """Create a user, optionally put it into one of the warehouse groups."""
    user = CustomUser.objects.create_user(
        email=email, first_name='Test', phone_number=phone, password='pass12345'
    )
    if group:
        user.groups.add(Group.objects.get(name=group))
    return user


def client_for(user):
    """API client authenticated as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def service_user(db):
    return make_user('service@test.com', '+380500000001', 'Service')


@pytest.fixture
def manager_user(db):
    return make_user('manager@test.com', '+380500000002', 'Warehouse Manager')


@pytest.fixture
def analyst_user(db):
    return make_user('analyst@test.com', '+380500000003', 'Analyst')


@pytest.fixture
def plain_user(db):
    return make_user('plain@test.com', '+380500000004')


@pytest.fixture
def service_api(service_user):
    return client_for(service_user)


@pytest.fixture
def manager_api(manager_user):
    return client_for(manager_user)


@pytest.fixture
def analyst_api(analyst_user):
    return client_for(analyst_user)


@pytest.fixture
def plain_api(plain_user):
    return client_for(plain_user)
