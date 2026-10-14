import pytest
from django.db.models import ProtectedError
from orders.models import Order
from orders.tests.factories import OrderFactory, OrderItemFactory


@pytest.mark.django_db
def test_order_str():
    order = OrderFactory()
    assert str(order) == f"Order {order.id}"


@pytest.mark.django_db
def test_order_default_status_is_pending():
    assert OrderFactory().status == Order.OrderStatus.PENDING


@pytest.mark.django_db
def test_order_item_get_total():
    item = OrderItemFactory(price=10, quantity=3)
    assert item.get_total() == 30


@pytest.mark.django_db
def test_order_get_total_cost():
    order = OrderFactory()
    OrderItemFactory(order=order, price=10, quantity=2)
    OrderItemFactory(order=order, price=5, quantity=3)
    assert order.get_total_cost() == 35


@pytest.mark.django_db
def test_order_get_total_cost_empty():
    assert OrderFactory().get_total_cost() == 0


@pytest.mark.django_db
def test_book_with_order_items_is_protected():
    item = OrderItemFactory()
    with pytest.raises(ProtectedError):
        item.book.delete()