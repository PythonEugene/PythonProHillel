import pytest
from unittest.mock import patch, MagicMock
from django.urls import reverse
from orders.tests.factories import OrderFactory, OrderItemFactory
from django.conf import settings
from django.core import mail
from orders.models import Order
from books.tests.factories import BookFactory

@pytest.mark.django_db
@patch("orders.views.stripe.checkout.Session.create")
def test_order_payment_redirects_to_stripe(mock_create, client):
    mock_create.return_value = MagicMock(id="cs_test_1", url="https://stripe.test/pay")
    order = OrderFactory()
    OrderItemFactory(order=order, price=10, quantity=2)

    response = client.get(reverse("orders:order_payment", args=[order.id]))

    assert response.status_code == 303
    assert response["Location"] == "https://stripe.test/pay"
    order.refresh_from_db()
    assert order.stripe_checkout_id == "cs_test_1"
    mock_create.assert_called_once()


@pytest.mark.django_db
def test_cart_add_puts_book_in_session(client):
    book = BookFactory()
    r = client.post(reverse("orders:cart_add", args=[book.id]), {"quantity": 2})
    assert r.status_code == 302
    assert client.session[settings.CART_SESSION_ID][str(book.id)]["quantity"] == 2


@pytest.mark.django_db
def test_cart_add_unknown_book_404(client):
    r = client.post(reverse("orders:cart_add", args=[9999]))
    assert r.status_code == 404


@pytest.mark.django_db
def test_cart_remove(client):
    book = BookFactory()
    client.post(reverse("orders:cart_add", args=[book.id]))
    client.get(reverse("orders:cart_remove", args=[book.id]))
    assert client.session[settings.CART_SESSION_ID] == {}


@pytest.mark.django_db
def test_order_create_empty_cart_redirects(client):
    r = client.get(reverse("orders:order_create"))
    assert r.status_code == 302
    assert r.url == reverse("orders:cart_detail")


@pytest.mark.django_db
def test_order_success_marks_paid(client):
    order = OrderFactory()
    r = client.get(reverse("orders:order_success", args=[order.id]))
    order.refresh_from_db()
    assert r.status_code == 200
    assert order.status == Order.OrderStatus.PAID


@pytest.mark.django_db
@patch("orders.views.stripe.Webhook.construct_event")
def test_webhook_marks_order_paid(mock_event, client):
    order = OrderFactory()
    mock_event.return_value = {
        "type": "checkout.session.completed",
        "data": {"object": {"metadata": {"order_id": str(order.id)}}},
    }
    r = client.post(reverse("orders:stripe_webhook"), data=b"{}",
                    content_type="application/json", HTTP_STRIPE_SIGNATURE="sig")
    order.refresh_from_db()
    assert r.status_code == 200
    assert order.status == Order.OrderStatus.PAID


@pytest.mark.django_db
@patch("orders.views.stripe.Webhook.construct_event", side_effect=ValueError)
def test_webhook_bad_payload_returns_400(mock_event, client):
    r = client.post(reverse("orders:stripe_webhook"), data=b"{}",
                    content_type="application/json", HTTP_STRIPE_SIGNATURE="sig")
    assert r.status_code == 400


@pytest.mark.django_db
def test_order_create_creates_order_and_sends_email(client):
    book = BookFactory(price=10)
    client.post(reverse("orders:cart_add", args=[book.id]), {"quantity": 2})
    r = client.post(reverse("orders:order_create"), {
        "first_name": "Ivan", "last_name": "Petrenko", "email": "ivan@test.com",
        "phone_number": "+380501234567", "address": "Kyiv",
    })
    order = Order.objects.get()
    assert r.status_code == 302
    assert order.total_price == 20
    assert order.items.count() == 1
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ["ivan@test.com"]