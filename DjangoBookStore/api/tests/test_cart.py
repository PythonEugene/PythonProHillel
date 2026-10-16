from decimal import Decimal
import pytest
from django.urls import reverse
from rest_framework.test import APIClient
from books.tests.factories import BookFactory

pytestmark = pytest.mark.django_db

LIST = 'api:cart-list'
ADD = 'api:cart-add'
REMOVE = 'api:cart-remove'
CLEAR = 'api:cart-clear'


def add(client, book, quantity=1, **extra):
    return client.post(
    reverse(ADD),
    {'book_id': book.id, 'quantity': quantity, **extra},
    format='json',
    )


# Generated with AI, reviewed and modified
def test_empty_cart(api_client):
    r = api_client.get(reverse(LIST))
    assert r.status_code == 200
    assert r.data['items'] == []
    assert r.data['total_items'] == 0
    assert Decimal(r.data['total_price']) == 0


# Generated with AI, reviewed and modified
def test_add_book_to_cart(api_client):
    book = BookFactory(price=Decimal('10.00'), stock=5)
    r = add(api_client, book, 2)
    assert r.status_code == 201
    assert len(r.data['items']) == 1
    assert r.data['items'][0]['book']['id'] == book.id
    assert r.data['total_items'] == 2
    assert Decimal(r.data['total_price']) == Decimal('20.00')


# Generated with AI, reviewed and modified
def test_adding_same_book_accumulates_quantity(api_client):
    book = BookFactory(stock=5)
    add(api_client, book, 1)
    r = add(api_client, book, 2)
    assert r.data['items'][0]['quantity'] == 3
    # the cart is kept in the session between requests
    assert api_client.get(reverse(LIST)).data['total_items'] == 3


# Generated with AI, reviewed and modified
def test_override_sets_exact_quantity(api_client):
    book = BookFactory(stock=5)
    add(api_client, book, 4)
    r = add(api_client, book, 1, override=True)
    assert r.data['items'][0]['quantity'] == 1


# Generated with AI, reviewed and modified
def test_cannot_add_more_than_stock(api_client):
    book = BookFactory(stock=2)
    r = add(api_client, book, 3)
    assert r.status_code == 400
    assert api_client.get(reverse(LIST)).data['items'] == []


# Generated with AI, reviewed and modified
def test_cumulative_quantity_cannot_exceed_stock(api_client):
    book = BookFactory(stock=3)
    add(api_client, book, 2)
    r = add(api_client, book, 2)
    assert r.status_code == 400
    assert api_client.get(reverse(LIST)).data['total_items'] == 2


# Generated with AI, reviewed and modified
def test_add_unknown_book_is_rejected(api_client):
    r = api_client.post(reverse(ADD), {'book_id': 9999, 'quantity': 1}, format='json')
    assert r.status_code == 400


# Generated with AI, reviewed and modified
def test_add_zero_quantity_is_rejected(api_client):
    r = add(api_client, BookFactory(), 0)
    assert r.status_code == 400


# Generated with AI, reviewed and modified
def test_remove_book_from_cart(api_client):
    book = BookFactory(stock=5)
    add(api_client, book, 1)
    r = api_client.post(reverse(REMOVE), {'book_id': book.id}, format='json')
    assert r.status_code == 200
    assert r.data['items'] == []


# Generated with AI, reviewed and modified
def test_clear_cart(api_client):
    add(api_client, BookFactory(stock=5), 1)
    add(api_client, BookFactory(stock=5), 1)
    r = api_client.post(reverse(CLEAR))
    assert r.status_code == 200
    assert r.data['total_items'] == 0


# Generated with AI, reviewed and modified
def test_carts_are_isolated_between_clients(api_client):
    add(api_client, BookFactory(stock=5), 1)
    stranger = APIClient()
    assert stranger.get(reverse(LIST)).data['total_items'] == 0


# Generated with AI, reviewed and modified
def test_deleted_book_is_skipped_in_cart(api_client):
    """A book removed from the catalog must not break the cart (see Cart.__iter__)."""
    book = BookFactory(stock=5)
    add(api_client, book, 1)
    book.delete()
    r = api_client.get(reverse(LIST))
    assert r.status_code == 200
    assert r.data['items'] == []