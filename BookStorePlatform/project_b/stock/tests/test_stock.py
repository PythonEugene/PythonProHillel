import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from stock.models import StockItem
from stock.tests.factories import StockItemFactory

pytestmark = pytest.mark.django_db

LIST = 'api:stock-list'
DETAIL = 'api:stock-detail'
RECEIVE = 'api:stock-receive'


def test_stock_list_requires_authentication(api_client):
    assert api_client.get(reverse(LIST)).status_code == 401


def test_user_without_group_cannot_read_stock(plain_api):
    assert plain_api.get(reverse(LIST)).status_code == 403


def test_analyst_can_list_and_retrieve_stock(analyst_api):
    StockItemFactory(book_id=1, on_hand=10, reserved=3)
    listing = analyst_api.get(reverse(LIST))
    assert listing.status_code == 200
    assert listing.data['count'] == 1

    detail = analyst_api.get(reverse(DETAIL, args=[1]))
    assert detail.status_code == 200
    assert detail.data['available'] == 7


def test_unknown_book_returns_404(analyst_api):
    assert analyst_api.get(reverse(DETAIL, args=[999])).status_code == 404


def test_analyst_cannot_receive_goods(analyst_api):
    r = analyst_api.post(reverse(RECEIVE, args=[1]), {'quantity': 5}, format='json')
    assert r.status_code == 403
    assert not StockItem.objects.exists()


def test_service_user_cannot_receive_goods(service_api):
    r = service_api.post(reverse(RECEIVE, args=[1]), {'quantity': 5}, format='json')
    assert r.status_code == 403


def test_manager_can_receive_goods(manager_api):
    payload = {'quantity': 10, 'title': 'Kobzar', 'note': 'first delivery'}
    r = manager_api.post(reverse(RECEIVE, args=[1]), payload, format='json')
    assert r.status_code == 200
    assert r.data['on_hand'] == 10
    assert r.data['available'] == 10
    assert StockItem.objects.get(book_id=1).title == 'Kobzar'


def test_receive_rejects_zero_quantity(manager_api):
    r = manager_api.post(reverse(RECEIVE, args=[1]), {'quantity': 0}, format='json')
    assert r.status_code == 400
    assert 'quantity' in r.data


def test_low_stock_filter(analyst_api):
    StockItemFactory(book_id=1, on_hand=3)  # available 3, low
    StockItemFactory(book_id=2, on_hand=50)  # plenty
    low = analyst_api.get(reverse(LIST), {'low_stock': 'true'})
    assert [item['book_id'] for item in low.data['results']] == [1]
    normal = analyst_api.get(reverse(LIST), {'low_stock': 'false'})
    assert [item['book_id'] for item in normal.data['results']] == [2]


def test_search_by_title(analyst_api):
    StockItemFactory(book_id=1, title='Python Basics')
    StockItemFactory(book_id=2, title='Cooking')
    r = analyst_api.get(reverse(LIST), {'search': 'python'})
    assert [item['book_id'] for item in r.data['results']] == [1]


def test_jwt_login_and_access(api_client, service_user):
    token = api_client.post(
        reverse('api:token_obtain_pair'),
        {'phone_number': service_user.phone_number, 'password': 'pass12345'},
        format='json',
    )
    assert token.status_code == 200

    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f'Bearer {token.data["access"]}')
    assert client.get(reverse(LIST)).status_code == 200


def test_invalid_bearer_token_is_rejected():
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION='Bearer not-a-real-token')
    assert client.get(reverse(LIST)).status_code == 401


def test_swagger_and_schema_are_available(api_client):
    assert api_client.get(reverse('api:docs')).status_code == 200
    assert api_client.get(reverse('api:schema')).status_code == 200


def test_health_check(api_client):
    r = api_client.get(reverse('health'))
    assert r.status_code == 200
    assert r.json()['status'] == 'ok'
