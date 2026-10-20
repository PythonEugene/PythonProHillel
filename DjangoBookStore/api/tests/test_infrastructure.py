from unittest.mock import patch
import pytest
from django.urls import reverse
from rest_framework.throttling import AnonRateThrottle

pytestmark = pytest.mark.django_db


# Generated with AI, reviewed and modified
def test_anonymous_requests_are_throttled(api_client):
    url = reverse('api:book-list')
    with patch.dict(AnonRateThrottle.THROTTLE_RATES, {'anon': '2/min'}):
        codes = [api_client.get(url).status_code for _ in range(3)]
    assert codes == [200, 200, 429]


# Generated with AI, reviewed and modified
def test_cors_allows_configured_origin(api_client):
    r = api_client.get(reverse('api:book-list'), HTTP_ORIGIN='http://localhost:3000')
    assert r.status_code == 200
    assert r['access-control-allow-origin'] == 'http://localhost:3000'


# Generated with AI, reviewed and modified
def test_cors_does_not_allow_unknown_origin(api_client):
    r = api_client.get(reverse('api:book-list'), HTTP_ORIGIN='http://evil.com')
    assert not r.has_header('access-control-allow-origin')


# Generated with AI, reviewed and modified
def test_swagger_docs_page_is_available(api_client):
    assert api_client.get(reverse('api:docs')).status_code == 200


# Generated with AI, reviewed and modified
def test_openapi_schema_is_generated(api_client):
    r = api_client.get(reverse('api:schema'))
    assert r.status_code == 200
