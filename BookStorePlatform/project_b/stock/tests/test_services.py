from datetime import timedelta
import pytest
from django.utils import timezone
from stock import services
from stock.models import Reservation, StockItem, StockMovement
from stock.tests.factories import StockItemFactory

pytestmark = pytest.mark.django_db


def lines(*pairs):
    """lines((1, 3), (2, 1)) -> [{'book_id': 1, 'quantity': 3}, {'book_id': 2, 'quantity': 1}]"""
    return [{'book_id': book_id, 'quantity': quantity} for book_id, quantity in pairs]


def test_reserve_holds_books():
    item = StockItemFactory(book_id=1, on_hand=10)
    reservation = services.reserve(1, lines((1, 3)))
    item.refresh_from_db()
    assert item.reserved == 3
    assert item.available == 7
    assert reservation.status == Reservation.Status.RESERVED
    assert reservation.items.get().quantity == 3


def test_reserve_is_idempotent_for_the_same_order():
    item = StockItemFactory(book_id=1, on_hand=10)
    first = services.reserve(1, lines((1, 3)))
    second = services.reserve(1, lines((1, 3)))
    item.refresh_from_db()
    assert first.pk == second.pk
    assert item.reserved == 3  # not 6
    assert Reservation.objects.count() == 1


def test_reserve_merges_duplicate_lines():
    item = StockItemFactory(book_id=1, on_hand=10)
    reservation = services.reserve(1, lines((1, 2), (1, 3)))
    item.refresh_from_db()
    assert item.reserved == 5
    assert reservation.items.count() == 1


def test_reserve_rejects_when_not_enough_stock():
    item = StockItemFactory(book_id=1, on_hand=2)
    with pytest.raises(services.InsufficientStock) as error:
        services.reserve(1, lines((1, 5)))
    assert error.value.shortages == [{'book_id': 1, 'requested': 5, 'available': 2}]
    item.refresh_from_db()
    assert item.reserved == 0
    assert not Reservation.objects.exists()


def test_reserve_unknown_book_counts_as_zero_available():
    with pytest.raises(services.InsufficientStock) as error:
        services.reserve(1, lines((99, 1)))
    assert error.value.shortages[0]['available'] == 0


def test_reserve_is_all_or_nothing():
    enough = StockItemFactory(book_id=1, on_hand=5)
    StockItemFactory(book_id=2, on_hand=1)
    with pytest.raises(services.InsufficientStock):
        services.reserve(1, lines((1, 2), (2, 3)))
    enough.refresh_from_db()
    assert enough.reserved == 0


def test_reserve_writes_movement():
    StockItemFactory(book_id=1, on_hand=10)
    services.reserve(7, lines((1, 3)))
    movement = StockMovement.objects.get()
    assert movement.kind == StockMovement.Kind.RESERVE
    assert movement.quantity == 3
    assert movement.order_id == 7


def test_reserve_for_released_order_is_rejected():
    StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 1)))
    services.release(1)
    with pytest.raises(services.InvalidReservationState):
        services.reserve(1, lines((1, 1)))


def test_confirm_ships_books():
    item = StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    reservation = services.confirm(1)
    item.refresh_from_db()
    assert reservation.status == Reservation.Status.CONFIRMED
    assert (item.on_hand, item.reserved) == (7, 0)
    assert StockMovement.objects.filter(kind=StockMovement.Kind.SHIP).count() == 1


def test_confirm_twice_ships_only_once():
    item = StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    services.confirm(1)
    services.confirm(1)
    item.refresh_from_db()
    assert item.on_hand == 7


def test_confirm_released_reservation_is_rejected():
    StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    services.release(1)
    with pytest.raises(services.InvalidReservationState):
        services.confirm(1)


def test_confirm_unknown_order():
    with pytest.raises(services.ReservationNotFound):
        services.confirm(404)


def test_release_gives_books_back():
    item = StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    reservation = services.release(1)
    item.refresh_from_db()
    assert reservation.status == Reservation.Status.RELEASED
    assert (item.on_hand, item.reserved) == (10, 0)


def test_release_twice_gives_back_only_once():
    item = StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    services.reserve(2, lines((1, 4)))
    services.release(1)
    services.release(1)
    item.refresh_from_db()
    assert item.reserved == 4  # only order 2 is still held


def test_release_of_confirmed_reservation_is_rejected():
    StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    services.confirm(1)
    with pytest.raises(services.InvalidReservationState):
        services.release(1)


def test_expire_reservations_releases_only_overdue_ones():
    item = StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 3)))
    services.reserve(2, lines((1, 2)))
    Reservation.objects.filter(order_id=1).update(expires_at=timezone.now() - timedelta(minutes=1))

    assert services.expire_reservations() == 1

    item.refresh_from_db()
    assert Reservation.objects.get(order_id=1).status == Reservation.Status.EXPIRED
    assert Reservation.objects.get(order_id=2).status == Reservation.Status.RESERVED
    assert item.reserved == 2


def test_receive_creates_and_updates_stock():
    services.receive(1, 5, title='First title')
    item = services.receive(1, 5, title='Second title', note='second delivery')
    assert item.on_hand == 10
    assert item.title == 'Second title'
    assert StockMovement.objects.filter(kind=StockMovement.Kind.RECEIVE).count() == 2


def test_receive_requires_positive_quantity():
    with pytest.raises(services.InvalidAdjustment):
        services.receive(1, 0)


def test_adjust_sets_quantity_and_logs_difference():
    StockItemFactory(book_id=1, on_hand=10)
    item = services.adjust(1, 8, note='inventory count')
    assert item.on_hand == 8
    assert StockMovement.objects.get(kind=StockMovement.Kind.ADJUST).quantity == -2


def test_adjust_cannot_go_below_reserved():
    StockItemFactory(book_id=1, on_hand=10)
    services.reserve(1, lines((1, 6)))
    with pytest.raises(services.InvalidAdjustment):
        services.adjust(1, 5)
    assert StockItem.objects.get(book_id=1).on_hand == 10


def test_adjust_unknown_book():
    with pytest.raises(services.StockItemNotFound):
        services.adjust(99, 5)
