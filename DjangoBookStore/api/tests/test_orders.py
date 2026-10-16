from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework.test import APIClient

from books.tests.factories import BookFactory
from orders.models import Order
from orders.tests.factories import OrderFactory, OrderItemFactory

pytestmark = pytest.mark.django_db

LIST = 'api:order-list'
DETAIL = 'api:order-detail'
CANCEL = 'api:order-cancel'


def client_for(user):
    """API client authenticated as the given user."""
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def order_payload(book, quantity=1, **extra):
    data = {
    'first_name': 'Ivan',
    'last_name': 'Petrenko',
    'email': 'ivan@test.com',
    'phone_number': '+380501234567',
    'address': 'Kyiv, Khreshchatyk 1',
    'items': [{'book_id': book.id, 'quantity': quantity}],
    }
    data.update(extra)
    return data


# Generated with AI, reviewed and modified
def test_orders_require_authentication(api_client):
    assert api_client.get(reverse(LIST)).status_code == 401


# Generated with AI, reviewed and modified
def test_create_order_calculates_total_on_server(user_api, user):
    book = BookFactory(price=Decimal('10.00'), stock=5)
    # the client tries to set its own total and status: both must be ignored
    payload = order_payload(book, 2, total_price='0.01', status='PAID')
    r = user_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 201
    order = Order.objects.get()
    assert order.total_price == Decimal('20.00')
    assert order.status == Order.OrderStatus.PENDING
    assert order.user == user
    assert len(r.data['items']) == 1
    assert r.data['items'][0]['book']['id'] == book.id
    assert Decimal(r.data['items'][0]['price']) == Decimal('10.00')


# Generated with AI, reviewed and modified
def test_create_order_rejects_empty_items(user_api):
    book = BookFactory()
    r = user_api.post(reverse(LIST), order_payload(book, items=[]), format='json')
    assert r.status_code == 400
    assert 'items' in r.data


# Generated with AI, reviewed and modified
def test_create_order_rejects_zero_quantity(user_api):
    r = user_api.post(reverse(LIST), order_payload(BookFactory(), 0), format='json')
    assert r.status_code == 400
    assert not Order.objects.exists()


# Generated with AI, reviewed and modified
def test_create_order_rejects_quantity_over_stock(user_api):
    book = BookFactory(stock=2)
    r = user_api.post(reverse(LIST), order_payload(book, 3), format='json')
    assert r.status_code == 400
    assert not Order.objects.exists()


# Generated with AI, reviewed and modified
def test_create_order_rejects_duplicate_books(user_api):
    book = BookFactory(stock=5)
    items = [{'book_id': book.id, 'quantity': 1}, {'book_id': book.id, 'quantity': 1}]
    r = user_api.post(reverse(LIST), order_payload(book, items=items), format='json')
    assert r.status_code == 400
    assert not Order.objects.exists()


# Generated with AI, reviewed and modified
def test_create_order_rejects_unknown_book(user_api):
    payload = order_payload(BookFactory(), items=[{'book_id': 9999, 'quantity': 1}])
    r = user_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 400


# Generated with AI, reviewed and modified
def test_create_order_requires_contact_data(user_api):
    payload = order_payload(BookFactory())
    del payload['address']
    r = user_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 400
    assert 'address' in r.data


# Generated with AI, reviewed and modified
def test_user_sees_only_own_orders(user_api, user, other_user):
    OrderFactory(user=user)
    OrderFactory(user=other_user)
    r = user_api.get(reverse(LIST))
    assert r.status_code == 200
    assert r.data['count'] == 1


# Generated with AI, reviewed and modified
def test_other_users_order_returns_404(user_api, other_user):
    order = OrderFactory(user=other_user)
    assert user_api.get(reverse(DETAIL, args=[order.id])).status_code == 404


# Generated with AI, reviewed and modified
def test_staff_sees_all_orders(admin_api, user, other_user):
    OrderFactory(user=user)
    OrderFactory(user=other_user)
    r = admin_api.get(reverse(LIST))
    assert r.data['count'] == 2


# Generated with AI, reviewed and modified
def test_filter_orders_by_status(user_api, user):
    OrderFactory(user=user, status=Order.OrderStatus.PAID)
    OrderFactory(user=user)
    r = user_api.get(reverse(LIST), {'status': 'PAID'})
    assert r.data['count'] == 1
    assert r.data['results'][0]['status'] == 'PAID'


# Generated with AI, reviewed and modified
def test_order_detail_contains_nested_items(user_api, user):
    order = OrderFactory(user=user)
    OrderItemFactory(order=order, price=10, quantity=2)
    r = user_api.get(reverse(DETAIL, args=[order.id]))
    assert r.status_code == 200
    item = r.data['items'][0]
    assert 'title' in item['book']
    assert Decimal(item['total']) == Decimal('20.00')


# Generated with AI, reviewed and modified
def test_owner_can_edit_contact_data(user_api, user):
    order = OrderFactory(user=user)
    r = user_api.patch(reverse(DETAIL, args=[order.id]), {'address': 'Lviv'}, format='json')
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.address == 'Lviv'


# Generated with AI, reviewed and modified
def test_staff_cannot_edit_someone_elses_order(admin_api, user):
    """IsOwnerOrReadOnly: staff may read an order but not change it."""
    order = OrderFactory(user=user)
    r = admin_api.patch(reverse(DETAIL, args=[order.id]), {'address': 'Hack'}, format='json')
    assert r.status_code == 403
    order.refresh_from_db()
    assert order.address != 'Hack'


# Generated with AI, reviewed and modified
def test_cannot_edit_order_that_is_not_pending(user_api, user):
    order = OrderFactory(user=user, status=Order.OrderStatus.PAID)
    r = user_api.patch(reverse(DETAIL, args=[order.id]), {'address': 'Lviv'}, format='json')
    assert r.status_code == 400


# Generated with AI, reviewed and modified
def test_owner_can_cancel_pending_order(user_api, user):
    order = OrderFactory(user=user)
    r = user_api.post(reverse(CANCEL, args=[order.id]))
    assert r.status_code == 200
    order.refresh_from_db()
    assert order.status == Order.OrderStatus.CANCELED


# Generated with AI, reviewed and modified
def test_cannot_cancel_order_twice(user_api, user):
    order = OrderFactory(user=user)
    user_api.post(reverse(CANCEL, args=[order.id]))
    r = user_api.post(reverse(CANCEL, args=[order.id]))
    assert r.status_code == 400


# Generated with AI, reviewed and modified
def test_cannot_cancel_someone_elses_order(other_user, user):
    order = OrderFactory(user=user)
    r = client_for(other_user).post(reverse(CANCEL, args=[order.id]))
    assert r.status_code == 404
    order.refresh_from_db()
    assert order.status == Order.OrderStatus.PENDING


# Generated with AI, reviewed and modified
def test_orders_cannot_be_deleted(user_api, user):
    order = OrderFactory(user=user)
    r = user_api.delete(reverse(DETAIL, args=[order.id]))
    assert r.status_code == 405
    assert Order.objects.filter(pk=order.pk).exists()