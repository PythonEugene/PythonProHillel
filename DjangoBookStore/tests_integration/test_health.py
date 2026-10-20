from unittest.mock import patch
import pytest
from django.db import OperationalError
from django.urls import reverse

pytestmark = pytest.mark.django_db


# Generated with AI, reviewed and modified
def test_health_ok(client):
    r = client.get(reverse('health'))
    assert r.status_code == 200
    assert r.json() == {'status': 'ok', 'database': 'ok', 'cache': 'ok'}


# Generated with AI, reviewed and modified
def test_health_reports_database_failure(client):
    with patch('DjangoBookStore.health.connection') as fake_connection:
        fake_connection.cursor.side_effect = OperationalError
        r = client.get(reverse('health'))
    assert r.status_code == 503
    assert r.json()['database'] == 'error'
    assert r.json()['status'] == 'error'


# Generated with AI, reviewed and modified
def test_health_rejects_post(client):
    assert client.post(reverse('health')).status_code == 405
