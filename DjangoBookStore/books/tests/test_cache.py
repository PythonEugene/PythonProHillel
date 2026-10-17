import pytest
from django.core.cache import cache
from django.urls import reverse
from books.cache_keys import book_cache_key, get_categories_version
from books.models import Book
from books.tests.factories import BookFactory, CategoryFactory

pytestmark = pytest.mark.django_db


# Generated with AI, reviewed and modified
def test_book_detail_served_from_cache_until_invalidated(
        client, django_capture_on_commit_callbacks):
    book = BookFactory(title='Old title')
    url = reverse('books:detail', args=[book.pk])
    assert 'Old title' in client.get(url).content.decode()

    Book.objects.filter(pk=book.pk).update(title='New title')  # update() не шлёт сигнал
    assert 'Old title' in client.get(url).content.decode()      # ответ из кеша

    with django_capture_on_commit_callbacks(execute=True):
        book.title = 'New title'
        book.save()                                              # сигнал сбрасывает кеш
    assert 'New title' in client.get(url).content.decode()


# Generated with AI, reviewed and modified
def test_new_book_appears_in_cached_catalog(client, django_capture_on_commit_callbacks):
    BookFactory(title='First book')
    assert 'First book' in client.get(reverse('books:list')).content.decode()

    with django_capture_on_commit_callbacks(execute=True):
        BookFactory(title='Second book')
    assert 'Second book' in client.get(reverse('books:list')).content.decode()


# Generated with AI, reviewed and modified
def test_deleting_book_clears_detail_cache(client, django_capture_on_commit_callbacks):
    book = BookFactory()
    client.get(reverse('books:detail', args=[book.pk]))
    assert cache.get(book_cache_key(book.pk)) is not None

    with django_capture_on_commit_callbacks(execute=True):
        book.delete()
    assert cache.get(book_cache_key(book.pk)) is None


# Generated with AI, reviewed and modified
def test_category_change_bumps_fragment_version(django_capture_on_commit_callbacks):
    category = CategoryFactory(name='Old')
    before = get_categories_version()
    with django_capture_on_commit_callbacks(execute=True):
        category.name = 'New'
        category.save()
    assert get_categories_version() != before


# Generated with AI, reviewed and modified
def test_category_change_clears_cached_books(client, django_capture_on_commit_callbacks):
    category = CategoryFactory(name='Old')
    book = BookFactory(category=category)
    client.get(reverse('books:detail', args=[book.pk]))
    assert cache.get(book_cache_key(book.pk)) is not None

    with django_capture_on_commit_callbacks(execute=True):
        category.name = 'New'
        category.save()
    assert cache.get(book_cache_key(book.pk)) is None