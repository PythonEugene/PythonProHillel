import pytest
import requests
import responses
from django.core.cache import cache
import json

from services.warehouse_client import (
    InvalidReservationState,
    OutOfStock,
    WarehouseClient,
    WarehouseClientError,
    WarehouseNotFound,
    WarehouseUnavailable,
)

BASE = 'http://warehouse.test/api/v1'
AUTH = 'http://warehouse.test/api/token/'
ITEMS = [{'book_id': 1, 'quantity': 2}]


@pytest.fixture(autouse=True)
def warehouse_settings(settings):
    settings.WAREHOUSE_SERVICE_URL = BASE
    settings.WAREHOUSE_AUTH_URL = AUTH
    settings.WAREHOUSE_SERVICE_USER = '+380000000000'
    settings.WAREHOUSE_SERVICE_PASSWORD = 'secret'
    settings.WAREHOUSE_TIMEOUT = 1
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api():
    with responses.RequestsMock(assert_all_requests_are_fired=False) as rsps:
        rsps.add(responses.POST, AUTH, json={'access': 'tok'})
        yield rsps


@pytest.fixture
def wh():
    return WarehouseClient()


def auth_calls(api):
    return [c for c in api.calls if c.request.url == AUTH]


def test_create_reservation_sends_token_and_payload(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/', json={'order_id': 5}, status=201)

    result = wh.create_reservation(5, ITEMS)

    assert result == {'order_id': 5}
    request = api.calls[-1].request
    assert request.headers['Authorization'] == 'Bearer tok'
    assert json.loads(request.body)['order_id'] == 5


def test_login_uses_phone_number(api, wh):
    api.add(responses.GET, f'{BASE}/stock/1/', json={})

    wh.get_stock(1)

    assert b'phone_number' in auth_calls(api)[0].request.body


def test_token_is_cached(api, wh):
    api.add(responses.GET, f'{BASE}/stock/1/', json={})

    wh.get_stock(1)
    wh.get_stock(1)

    assert len(auth_calls(api)) == 1


def test_expired_token_is_refreshed_once(api, wh):
    api.add(responses.GET, f'{BASE}/stock/1/', status=401)
    api.add(responses.GET, f'{BASE}/stock/1/', json={'book_id': 1})

    assert wh.get_stock(1) == {'book_id': 1}
    assert len(auth_calls(api)) == 2


def test_second_401_raises_client_error(api, wh):
    api.add(responses.GET, f'{BASE}/stock/1/', status=401)
    api.add(responses.GET, f'{BASE}/stock/1/', status=401)

    with pytest.raises(WarehouseClientError):
        wh.get_stock(1)


def test_insufficient_stock_raises_out_of_stock(api, wh):
    shortages = [{'book_id': 1, 'requested': 2, 'available': 0}]
    api.add(
        responses.POST,
        f'{BASE}/reservations/',
        status=409,
        json={'code': 'insufficient_stock', 'shortages': shortages},
    )

    with pytest.raises(OutOfStock) as exc:
        wh.create_reservation(5, ITEMS)

    assert exc.value.shortages == shortages


def test_invalid_state_raises(api, wh):
    api.add(
        responses.POST,
        f'{BASE}/reservations/5/confirm/',
        status=409,
        json={'code': 'invalid_state', 'detail': 'already released'},
    )

    with pytest.raises(InvalidReservationState):
        wh.confirm(5)


def test_404_raises_not_found(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/5/release/', status=404, json={})

    with pytest.raises(WarehouseNotFound):
        wh.release(5)


def test_400_raises_client_error(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/', status=400, json={'items': ['bad']})

    with pytest.raises(WarehouseClientError):
        wh.create_reservation(5, ITEMS)


def test_500_raises_unavailable(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/', status=500, body='oops')

    with pytest.raises(WarehouseUnavailable):
        wh.create_reservation(5, ITEMS)


def test_connection_error_raises_unavailable(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/', body=requests.ConnectionError('down'))

    with pytest.raises(WarehouseUnavailable):
        wh.create_reservation(5, ITEMS)


def test_auth_failure_raises_unavailable(wh):
    with responses.RequestsMock() as rsps:
        rsps.add(responses.POST, AUTH, body=requests.ConnectionError('down'))
        with pytest.raises(WarehouseUnavailable):
            wh.get_stock(1)


def test_empty_response_body_returns_empty_dict(api, wh):
    api.add(responses.POST, f'{BASE}/reservations/5/release/', status=204)

    assert wh.release(5) == {}


@pytest.mark.parametrize(
    'call, method, path',
    [
        (lambda c: c.get_stock(5), responses.GET, '/stock/5/'),
        (lambda c: c.confirm(7), responses.POST, '/reservations/7/confirm/'),
        (lambda c: c.release(7), responses.POST, '/reservations/7/release/'),
        (lambda c: c.receive(5, 10, 'Book'), responses.POST, '/stock/5/receive/'),
    ],
)
def test_endpoints(api, wh, call, method, path):
    api.add(method, f'{BASE}{path}', json={'ok': True})

    assert call(wh) == {'ok': True}