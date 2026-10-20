import pytest
from django.urls import reverse
from books.tests.factories import BookFactory, CategoryFactory

pytestmark = pytest.mark.django_db


# Generated with AI, reviewed and modified
def test_category_list_has_books_count(api_client):
    category = CategoryFactory()
    BookFactory.create_batch(2, category=category)
    r = api_client.get(reverse('api:category-list'))
    assert r.status_code == 200
    assert r.data['results'][0]['books_count'] == 2


# Generated with AI, reviewed and modified
def test_category_detail_includes_books(api_client):
    category = CategoryFactory()
    BookFactory.create_batch(2, category=category)
    r = api_client.get(reverse('api:category-detail', args=[category.id]))
    assert r.status_code == 200
    assert len(r.data['books']) == 2


# Generated with AI, reviewed and modified
def test_regular_user_cannot_create_category(user_api):
    r = user_api.post(
        reverse('api:category-list'), {'name': 'Fantasy', 'slug': 'fantasy'}, format='json'
    )
    assert r.status_code == 403


# Generated with AI, reviewed and modified
def test_admin_can_create_category(admin_api):
    r = admin_api.post(
        reverse('api:category-list'), {'name': 'Fantasy', 'slug': 'fantasy'}, format='json'
    )
    assert r.status_code == 201
    assert r.data['slug'] == 'fantasy'
