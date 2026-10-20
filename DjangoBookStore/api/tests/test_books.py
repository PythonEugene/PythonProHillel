from decimal import Decimal
import pytest
from django.urls import reverse
from books.models import Book
from books.tests.factories import BookFactory, CategoryFactory

pytestmark = pytest.mark.django_db

LIST = 'api:book-list'
DETAIL = 'api:book-detail'


# Generated with AI, reviewed and modified
def test_list_is_public(api_client):
    BookFactory.create_batch(3)
    r = api_client.get(reverse(LIST))
    assert r.status_code == 200
    assert r.data['count'] == 3


# Generated with AI, reviewed and modified
def test_list_is_paginated_by_20(api_client):
    BookFactory.create_batch(21, category=CategoryFactory())
    first = api_client.get(reverse(LIST))
    assert len(first.data['results']) == 20
    assert first.data['next'] is not None
    second = api_client.get(reverse(LIST), {'page': 2})
    assert len(second.data['results']) == 1


# Generated with AI, reviewed and modified
def test_detail_contains_nested_category(api_client):
    book = BookFactory()
    r = api_client.get(reverse(DETAIL, args=[book.id]))
    assert r.status_code == 200
    assert r.data['category']['slug'] == book.category.slug


# Generated with AI, reviewed and modified
def test_detail_unknown_book_returns_404(api_client):
    assert api_client.get(reverse(DETAIL, args=[9999])).status_code == 404


# Generated with AI, reviewed and modified
def test_filter_by_price_range(api_client):
    BookFactory(price=Decimal('5.00'))
    BookFactory(price=Decimal('50.00'))
    r = api_client.get(reverse(LIST), {'price_min': 10})
    assert r.data['count'] == 1
    assert Decimal(r.data['results'][0]['price']) == Decimal('50.00')


# Generated with AI, reviewed and modified
def test_filter_in_stock(api_client):
    BookFactory(stock=0)
    BookFactory(stock=3)
    r = api_client.get(reverse(LIST), {'in_stock': 'true'})
    assert r.data['count'] == 1


# Generated with AI, reviewed and modified
def test_search_by_title(api_client):
    BookFactory(title='Python Basics')
    BookFactory(title='Cooking')
    r = api_client.get(reverse(LIST), {'search': 'python'})
    assert [b['title'] for b in r.data['results']] == ['Python Basics']


# Generated with AI, reviewed and modified
def test_ordering_by_price_descending(api_client):
    for price in ('10.00', '30.00', '20.00'):
        BookFactory(price=Decimal(price))
    r = api_client.get(reverse(LIST), {'ordering': '-price'})
    prices = [Decimal(b['price']) for b in r.data['results']]
    assert prices == sorted(prices, reverse=True)


# Generated with AI, reviewed and modified
def test_anonymous_cannot_create_book(api_client):
    r = api_client.post(reverse(LIST), {}, format='json')
    assert r.status_code == 401


# Generated with AI, reviewed and modified
def test_regular_user_cannot_create_book(user_api):
    category = CategoryFactory()
    payload = {
        'title': 'X',
        'author': 'Y',
        'price': '10.00',
        'stock': 1,
        'category_id': category.id,
    }
    r = user_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 403
    assert not Book.objects.exists()


# Generated with AI, reviewed and modified
def test_admin_can_create_book(admin_api):
    category = CategoryFactory()
    payload = {
        'title': 'Kobzar',
        'author': 'Shevchenko',
        'price': '12.50',
        'stock': 3,
        'category_id': category.id,
    }
    r = admin_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 201
    assert r.data['category']['id'] == category.id
    assert Book.objects.get(title='Kobzar').price == Decimal('12.50')


# Generated with AI, reviewed and modified
def test_create_book_with_non_positive_price_is_rejected(admin_api):
    category = CategoryFactory()
    payload = {'title': 'X', 'author': 'Y', 'price': '0', 'stock': 1, 'category_id': category.id}
    r = admin_api.post(reverse(LIST), payload, format='json')
    assert r.status_code == 400
    assert 'price' in r.data


# Generated with AI, reviewed and modified
def test_admin_can_update_and_delete_book(admin_api):
    book = BookFactory()
    r = admin_api.patch(reverse(DETAIL, args=[book.id]), {'title': 'New'}, format='json')
    assert r.status_code == 200
    book.refresh_from_db()
    assert book.title == 'New'

    r = admin_api.delete(reverse(DETAIL, args=[book.id]))
    assert r.status_code == 204
    assert not Book.objects.filter(pk=book.pk).exists()
