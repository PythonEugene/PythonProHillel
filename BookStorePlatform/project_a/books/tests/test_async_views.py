import pytest
from asgiref.sync import sync_to_async
from django.urls import reverse
from books.tests.factories import BookFactory

pytestmark = pytest.mark.django_db(transaction=True)


async def test_stats_api(async_client):
    await sync_to_async(BookFactory.create_batch)(3)
    r = await async_client.get(reverse("books:api_stats"))
    assert r.json() == {"books": 3, "categories": 3}


async def test_books_api_list(async_client):
    await sync_to_async(BookFactory.create_batch)(2)
    r = await async_client.get(reverse("books:books_api"))
    data = r.json()["books"]
    assert len(data) == 2
    assert {"id", "title", "category"} <= set(data[0])


async def test_book_detail_api(async_client):
    book = await sync_to_async(BookFactory)(title="Kobzar")
    r = await async_client.get(reverse("books:book_detail_api", args=[book.id]))
    assert r.json()["title"] == "Kobzar"


async def test_book_detail_api_404(async_client):
    r = await async_client.get(reverse("books:book_detail_api", args=[9999]))
    assert r.status_code == 404
