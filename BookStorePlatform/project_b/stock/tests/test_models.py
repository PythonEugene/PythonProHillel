from datetime import timedelta

import pytest
from django.contrib.auth.models import Group
from django.db import IntegrityError, transaction
from django.utils import timezone

from stock.models import Reservation
from stock.tests.factories import ReservationFactory, ReservationItemFactory, StockItemFactory

pytestmark = pytest.mark.django_db


def test_available_is_on_hand_minus_reserved():
    item = StockItemFactory(on_hand=10, reserved=3)
    assert item.available == 7


def test_is_low_follows_threshold(settings):
    settings.LOW_STOCK_THRESHOLD = 5
    assert StockItemFactory(on_hand=6, reserved=1).is_low is True  # available == 5
    assert StockItemFactory(on_hand=20, reserved=0).is_low is False


def test_reserved_cannot_exceed_on_hand():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockItemFactory(on_hand=2, reserved=3)


def test_book_id_is_unique():
    StockItemFactory(book_id=7)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            StockItemFactory(book_id=7)


def test_stock_item_str():
    assert str(StockItemFactory(book_id=5, title='Kobzar')) == '#5 Kobzar'


def test_reservation_default_expiry_uses_ttl(settings):
    settings.RESERVATION_TTL_MINUTES = 30
    reservation = ReservationFactory()
    left = reservation.expires_at - timezone.now()
    assert timedelta(minutes=29) < left <= timedelta(minutes=30)


def test_reservation_is_expired_only_when_reserved_and_late():
    late = timezone.now() - timedelta(minutes=1)
    assert ReservationFactory(expires_at=late).is_expired is True
    paid = ReservationFactory(expires_at=late, status=Reservation.Status.CONFIRMED)
    assert paid.is_expired is False
    assert ReservationFactory().is_expired is False


def test_same_book_cannot_be_twice_in_one_reservation():
    reservation = ReservationFactory()
    ReservationItemFactory(reservation=reservation, book_id=1)
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ReservationItemFactory(reservation=reservation, book_id=1)


def test_reservation_quantity_must_be_positive():
    with pytest.raises(IntegrityError):
        with transaction.atomic():
            ReservationItemFactory(quantity=0)


def test_groups_exist_with_expected_permissions():
    names = set(Group.objects.values_list('name', flat=True))
    assert {'Service', 'Warehouse Manager', 'Analyst'} <= names

    def perms(group):
        return set(Group.objects.get(name=group).permissions.values_list('codename', flat=True))

    assert 'reserve_stock' in perms('Service')
    assert 'adjust_stock' not in perms('Service')
    assert 'adjust_stock' in perms('Warehouse Manager')
    assert 'view_reports' in perms('Analyst')
    assert 'adjust_stock' not in perms('Analyst')
