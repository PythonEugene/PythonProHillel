import logging
import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)
TOKEN_KEY = 'warehouse_access_token'


class WarehouseClientError(Exception): ...
class WarehouseUnavailable(WarehouseClientError): ...
class WarehouseNotFound(WarehouseClientError): ...
class InvalidReservationState(WarehouseClientError): ...

class OutOfStock(WarehouseClientError):
    def __init__(self, shortages=None):
        self.shortages = shortages or []
        super().__init__(f'Not enough stock: {self.shortages}')


class WarehouseClient:
    def __init__(self):
        self.base_url = settings.WAREHOUSE_SERVICE_URL.rstrip('/')
        self.auth_url = settings.WAREHOUSE_AUTH_URL
        self.timeout = settings.WAREHOUSE_TIMEOUT
        self.session = requests.Session()

    def _token(self):
        token = cache.get(TOKEN_KEY)
        if not token:
            try:
                r = self.session.post(self.auth_url, timeout=self.timeout, json={
                    'phone_number': settings.WAREHOUSE_SERVICE_USER,
                    'password': settings.WAREHOUSE_SERVICE_PASSWORD})
                r.raise_for_status()
            except requests.RequestException as e:
                logger.error('Warehouse auth failed: %s', e)
                raise WarehouseUnavailable(str(e)) from e
            token = r.json()['access']
            cache.set(TOKEN_KEY, token, 25 * 60)  # access живёт 30 мин
        return token

    def _request(self, method, path, **kwargs):
        for attempt in (1, 2):
            try:
                r = self.session.request(
                    method, f'{self.base_url}{path}', timeout=self.timeout,
                    headers={'Authorization': f'Bearer {self._token()}'}, **kwargs)
            except requests.RequestException as e:
                logger.error('Warehouse unreachable: %s', e)
                raise WarehouseUnavailable(str(e)) from e
            if r.status_code == 401 and attempt == 1:
                cache.delete(TOKEN_KEY)
                continue
            if r.status_code == 409:
                body = r.json() if r.content else {}
                if body.get('code') == 'insufficient_stock':
                    raise OutOfStock(body.get('shortages'))
                raise InvalidReservationState(body.get('detail', r.text))
            if r.status_code == 404:
                raise WarehouseNotFound(r.text)
            if r.status_code >= 500:
                logger.error('Warehouse %s: %s', r.status_code, r.text[:200])
                raise WarehouseUnavailable(f'HTTP {r.status_code}')
            if r.status_code >= 400:
                raise WarehouseClientError(f'HTTP {r.status_code}: {r.text[:200]}')
            return r.json() if r.content else {}

    def create_reservation(self, order_id, items):
        return self._request('POST', '/reservations/',
                             json={'order_id': order_id, 'items': items})

    def confirm(self, order_id):
        return self._request('POST', f'/reservations/{order_id}/confirm/')

    def release(self, order_id):
        return self._request('POST', f'/reservations/{order_id}/release/')

    def get_stock(self, book_id):
        return self._request('GET', f'/stock/{book_id}/')

    def receive(self, book_id, quantity, title=''):
        return self._request(
            'POST',
            f'/stock/{book_id}/receive/',
            json = {'quantity': quantity, 'title': title},
        )