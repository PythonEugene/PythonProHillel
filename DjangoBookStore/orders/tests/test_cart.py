import pytest
from decimal import Decimal
from orders.cart import Cart
from books.tests.factories import BookFactory


class FakeSession(dict):
    modified = False


class FakeRequest:
    def __init__(self):
        self.session = FakeSession()


@pytest.fixture
def cart():
    return Cart(FakeRequest())


@pytest.mark.django_db
def test_add_book(cart):
    book = BookFactory()
    cart.add(book, quantity=2)
    assert len(cart) == 2


@pytest.mark.django_db
def test_add_same_book_accumulates(cart):
    book = BookFactory()
    cart.add(book, 1)
    cart.add(book, 3)
    assert len(cart) == 4


@pytest.mark.django_db
def test_add_non_positive_quantity_becomes_one(cart):
    cart.add(BookFactory(), quantity=0)
    assert len(cart) == 1


@pytest.mark.django_db
def test_override_quantity(cart):
    book = BookFactory()
    cart.add(book, 5)
    cart.add(book, 2, override_quantity=True)
    assert len(cart) == 2


@pytest.mark.django_db
def test_remove_book(cart):
    book = BookFactory()
    cart.add(book)
    cart.remove(book)
    assert len(cart) == 0


@pytest.mark.django_db
def test_total_price(cart):
    cart.add(BookFactory(price=Decimal("10.00")), 2)
    cart.add(BookFactory(price=Decimal("5.50")), 1)
    assert cart.get_total_price() == Decimal("25.50")


@pytest.mark.django_db
def test_clear(cart):
    cart.add(BookFactory())
    cart.clear()
    assert len(cart) == 0