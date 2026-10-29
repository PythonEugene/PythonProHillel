import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from django.conf import settings
from django.contrib.auth.models import Permission
from django.core import mail
from django.urls import reverse
from books.models import Book
from books.tests.factories import BookFactory, CategoryFactory
from orders.models import Order
from users.models import CustomUser
from users.tests.factories import UserFactory

pytestmark = pytest.mark.django_db

REG = {
    "email": "new@test.com",
    "phone_number": "+380502222222",
    "first_name": "Ivan",
    "last_name": "P",
    "password1": "Str0ngPass!234",
    "password2": "Str0ngPass!234",
}
ORDER = {
    "first_name": "Ivan",
    "last_name": "Petrenko",
    "email": "ivan@test.com",
    "phone_number": "+380501234567",
    "address": "Kyiv",
}


def add_to_cart(client, book, qty=1):
    return client.post(reverse("orders:cart_add", args=[book.id]), {"quantity": qty})


def test_register_then_login(client):
    r = client.post(reverse("users:register"), REG)
    assert r.status_code == 302 and r.url == reverse("users:login")
    assert CustomUser.objects.filter(email="new@test.com").exists()
    r = client.post(
        reverse("users:login"), {"username": REG["phone_number"], "password": REG["password1"]}
    )
    assert r.status_code == 302
    assert "_auth_user_id" in client.session


def test_register_duplicate_shows_errors(client):
    client.post(reverse("users:register"), REG)
    r = client.post(reverse("users:register"), REG)
    assert r.status_code == 200
    assert CustomUser.objects.count() == 1


def test_login_wrong_password(client, user):
    r = client.post(reverse("users:login"), {"username": user.phone_number, "password": "wrong"})
    assert r.status_code == 200
    assert "_auth_user_id" not in client.session


def test_logout(auth_client):
    r = auth_client.post(reverse("users:logout"))
    assert r.url == reverse("books:list")
    assert "_auth_user_id" not in auth_client.session


def test_catalog_to_detail(client):
    book = BookFactory(title="Kobzar")
    assert "Kobzar" in client.get(reverse("books:list")).content.decode()
    r = client.get(reverse("books:detail", args=[book.id]))
    assert r.status_code == 200 and "Kobzar" in r.content.decode()


def test_filter_by_category(client):
    a, b = CategoryFactory(), CategoryFactory()
    book_a = BookFactory(category=a)
    BookFactory(category=b)
    r = client.get(reverse("books:list"), {"category": a.slug})
    assert list(r.context["books"]) == [book_a]


def test_search_by_title(client):
    BookFactory(title="Python Basics")
    BookFactory(title="Cooking")
    r = client.get(reverse("books:list"), {"q": "python"})
    assert [b.title for b in r.context["books"]] == ["Python Basics"]


def test_pagination(client):
    BookFactory.create_batch(16, category=CategoryFactory())
    assert len(client.get(reverse("books:list")).context["books"]) == 15
    assert len(client.get(reverse("books:list"), {"page": 2}).context["books"]) == 1


def test_create_book_anonymous_redirected(client):
    r = client.post(reverse("books:add"), {"title": "X"})
    assert r.status_code == 302
    assert "login" in r.url
    assert not Book.objects.exists()


def test_create_book(auth_client, user):
    user.user_permissions.add(Permission.objects.get(codename="add_book"))
    cat = CategoryFactory()
    r = auth_client.post(
        reverse("books:add"),
        {
            "title": "Kobzar",
            "author": "Shevchenko",
            "price": "12.50",
            "description": "",
            "category": cat.id,
            "stock": 3,
        },
    )
    assert r.status_code == 302
    assert Book.objects.get(title="Kobzar").price == Decimal("12.50")


def test_edit_book_without_permission_forbidden(auth_client):
    book = BookFactory()
    r = auth_client.post(reverse("books:edit", args=[book.id]), {"title": "Hack"})
    assert r.status_code == 403


def test_edit_book(auth_client, user):
    user.user_permissions.add(Permission.objects.get(codename="change_book"))
    book = BookFactory()
    auth_client.post(
        reverse("books:edit", args=[book.id]),
        {
            "title": "New title",
            "author": book.author,
            "price": "9.99",
            "description": "",
            "category": book.category_id,
            "stock": 1,
        },
    )
    book.refresh_from_db()
    assert book.title == "New title"


def test_delete_anonymous_not_allowed(client):
    book = BookFactory()
    client.post(reverse("books:delete", args=[book.id]))
    assert Book.objects.filter(pk=book.pk).exists()


def test_delete_without_permission_forbidden(auth_client):
    book = BookFactory()
    r = auth_client.post(reverse("books:delete", args=[book.id]))
    assert r.status_code == 403
    assert Book.objects.filter(pk=book.pk).exists()


def test_delete_with_permission(auth_client, user):
    user.user_permissions.add(Permission.objects.get(codename="delete_book"))
    book = BookFactory()
    r = auth_client.post(reverse("books:delete", args=[book.id]))
    assert r.status_code == 302
    assert not Book.objects.filter(pk=book.pk).exists()


@patch("orders.views.stripe.checkout.Session.create")
@patch("orders.views.stripe.checkout.Session.retrieve")
def test_full_purchase_flow(mock_retrieve, mock_create, auth_client, user):
    mock_create.return_value = MagicMock(id="cs_1", url="https://stripe.test/pay")
    mock_retrieve.return_value = MagicMock(payment_status='paid')

    book = BookFactory(price=Decimal("10.00"))
    add_to_cart(auth_client, book, 2)

    assert auth_client.get(reverse("orders:cart_detail")).status_code == 200

    r = auth_client.post(reverse("orders:order_create"), ORDER)
    order = Order.objects.get()
    assert r.url == reverse("orders:order_payment", args=[order.id])

    r = auth_client.get(r.url)
    assert r.status_code == 303 and r.url == "https://stripe.test/pay"

    auth_client.get(reverse("orders:order_success", args=[order.id]))
    order.refresh_from_db()
    assert order.status == Order.OrderStatus.PAID
    assert order.user == user
    assert len(mail.outbox) == 1
    assert auth_client.session[settings.CART_SESSION_ID] == {}


def test_anonymous_order_with_two_books(client):
    add_to_cart(client, BookFactory(price=Decimal("10.00")), 2)
    add_to_cart(client, BookFactory(price=Decimal("5.50")))
    client.post(reverse("orders:order_create"), ORDER)
    order = Order.objects.get()
    assert order.user is None
    assert order.total_price == Decimal("25.50")
    assert order.items.count() == 2


@patch("orders.views.stripe.Webhook.construct_event")
def test_order_then_webhook_marks_paid(mock_event, client):
    add_to_cart(client, BookFactory())
    client.post(reverse("orders:order_create"), ORDER)
    order = Order.objects.get()
    mock_event.return_value = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"order_id": str(order.id)}}},
    }
    r = client.post(
        reverse("orders:stripe_webhook"),
        data=b"{}",
        content_type="application/json",
        HTTP_STRIPE_SIGNATURE="sig",
    )
    order.refresh_from_db()
    assert r.status_code == 200 and order.status == Order.OrderStatus.PAID


def test_manage_permissions_forbidden_without_perm(client):
    target = UserFactory()
    client.force_login(UserFactory())
    r = client.get(reverse("users:manage_permissions", args=[target.id]))
    assert r.status_code == 403


def test_manage_permissions_update(client):
    manager, target = UserFactory(), UserFactory()
    manager.user_permissions.add(
        *Permission.objects.filter(
            codename__in=["can_see_user_permissions", "can_set_user_permissions"]
        )
    )
    perm = Permission.objects.get(codename="add_book")
    client.force_login(manager)
    r = client.post(
        reverse("users:manage_permissions", args=[target.id]), {"permissions": [perm.id]}
    )
    assert r.status_code == 302
    assert list(target.user_permissions.all()) == [perm]
