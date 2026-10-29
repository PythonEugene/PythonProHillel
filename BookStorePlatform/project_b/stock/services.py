"""Business logic of the warehouse.

Views, the admin and Celery tasks only call these functions.
"""

import logging

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Reservation, ReservationItem, StockItem, StockMovement

logger = logging.getLogger(__name__)


class StockError(Exception):
    """Base class of warehouse business errors."""


class InsufficientStock(StockError):
    """Not enough free books for a reservation."""

    def __init__(self, shortages):
        self.shortages = shortages
        super().__init__('Not enough stock')


class InvalidReservationState(StockError):
    """The operation is not allowed in the current state of the reservation."""


class ReservationNotFound(StockError):
    """There is no reservation for this order."""


class StockItemNotFound(StockError):
    """The warehouse has no record of this book."""


class InvalidAdjustment(StockError):
    """The requested change of stock is not possible."""


def _log(item, kind, quantity, order_id=None, user=None, note=''):
    """Write one line to the stock movement journal."""
    StockMovement.objects.create(
        stock_item=item,
        kind=kind,
        quantity=quantity,
        order_id=order_id,
        created_by=user,
        note=note,
    )


def _lock_reservation(order_id):
    """Load a reservation and lock its row until the end of the transaction."""
    try:
        return Reservation.objects.select_for_update().get(order_id=order_id)
    except Reservation.DoesNotExist:
        raise ReservationNotFound(f'No reservation for order {order_id}') from None


@transaction.atomic
def reserve(order_id, items, user=None):
    """Reserve books for an order.
    `items` is a list of {'book_id': int, 'quantity': int}. Calling the function
    again for the same order returns the existing reservation (idempotent).
    Raises InsufficientStock when some books are not available.
    """
    existing = Reservation.objects.select_for_update().filter(order_id=order_id).first()
    if existing is not None:
        if existing.status in (Reservation.Status.RESERVED, Reservation.Status.CONFIRMED):
            return existing
        raise InvalidReservationState(f'Reservation for order {order_id} is {existing.status}')

    quantities = {}
    for line in items:
        quantities[line['book_id']] = quantities.get(line['book_id'], 0) + line['quantity']

    stock = {
        item.book_id: item
        for item in StockItem.objects.select_for_update()
        .filter(book_id__in=quantities)
        .order_by('book_id')
    }

    shortages = []
    for book_id, quantity in quantities.items():
        available = stock[book_id].available if book_id in stock else 0
        if available < quantity:
            shortages.append({'book_id': book_id, 'requested': quantity, 'available': available})
    if shortages:
        logger.warning('Reservation for order %s rejected: %s', order_id, shortages)
        raise InsufficientStock(shortages)

    try:
        with transaction.atomic():
            reservation = Reservation.objects.create(order_id=order_id)
    except IntegrityError:  # another request created it a moment ago
        return Reservation.objects.get(order_id=order_id)

    for book_id, quantity in quantities.items():
        ReservationItem.objects.create(reservation=reservation, book_id=book_id, quantity=quantity)
        item = stock[book_id]
        item.reserved += quantity
        item.save(update_fields=['reserved', 'updated_at'])
        _log(item, StockMovement.Kind.RESERVE, quantity, order_id, user)

    logger.info('Reserved %s book(s) for order %s', len(quantities), order_id)
    return reservation


@transaction.atomic
def confirm(order_id, user=None):
    """The order is paid: books leave the warehouse (on hand and reserved go down)."""
    reservation = _lock_reservation(order_id)
    if reservation.status == Reservation.Status.CONFIRMED:
        return reservation
    if reservation.status != Reservation.Status.RESERVED:
        raise InvalidReservationState(
            f'Reservation for order {order_id} is {reservation.status} and cannot be confirmed'
        )

    for line in reservation.items.order_by('book_id'):
        item = StockItem.objects.select_for_update().get(book_id=line.book_id)
        item.on_hand -= line.quantity
        item.reserved -= line.quantity
        item.save(update_fields=['on_hand', 'reserved', 'updated_at'])
        _log(item, StockMovement.Kind.SHIP, line.quantity, order_id, user)

    reservation.status = Reservation.Status.CONFIRMED
    reservation.save(update_fields=['status', 'updated_at'])
    logger.info('Confirmed reservation of order %s', order_id)
    return reservation


@transaction.atomic
def release(order_id, user=None, new_status=Reservation.Status.RELEASED):
    """The order is canceled (or the time is over): give the reserved books back."""
    reservation = _lock_reservation(order_id)
    if reservation.status in (Reservation.Status.RELEASED, Reservation.Status.EXPIRED):
        return reservation
    if reservation.status == Reservation.Status.CONFIRMED:
        raise InvalidReservationState(
            f'Reservation for order {order_id} is already confirmed and cannot be released'
        )

    for line in reservation.items.order_by('book_id'):
        item = StockItem.objects.select_for_update().get(book_id=line.book_id)
        item.reserved -= line.quantity
        item.save(update_fields=['reserved', 'updated_at'])
        _log(item, StockMovement.Kind.RELEASE, line.quantity, order_id, user)

    reservation.status = new_status
    reservation.save(update_fields=['status', 'updated_at'])
    logger.info('Released reservation of order %s (%s)', order_id, new_status)
    return reservation


def expire_reservations():
    """Release every unpaid reservation whose time is over. Returns how many were released."""
    order_ids = list(
        Reservation.objects.filter(
            status=Reservation.Status.RESERVED, expires_at__lte=timezone.now()
        ).values_list('order_id', flat=True)
    )
    released = 0
    for order_id in order_ids:
        try:
            release(order_id, new_status=Reservation.Status.EXPIRED)
            released += 1
        except StockError:
            logger.exception('Could not expire reservation of order %s', order_id)
    return released


@transaction.atomic
def receive(book_id, quantity, user=None, title='', note=''):
    """Register a delivery: on hand goes up. The stock record is created if needed."""
    if quantity <= 0:
        raise InvalidAdjustment('Quantity must be positive')

    item, _created = StockItem.objects.select_for_update().get_or_create(
        book_id=book_id, defaults={'title': title}
    )
    item.on_hand += quantity
    update_fields = ['on_hand', 'updated_at']
    if title and item.title != title:
        item.title = title
        update_fields.append('title')
    item.save(update_fields=update_fields)
    _log(item, StockMovement.Kind.RECEIVE, quantity, user=user, note=note)
    logger.info('Received %s x book %s', quantity, book_id)
    return item


@transaction.atomic
def adjust(book_id, on_hand, user=None, note=''):
    """Set the exact quantity on hand (for example after an inventory count)."""
    try:
        item = StockItem.objects.select_for_update().get(book_id=book_id)
    except StockItem.DoesNotExist:
        raise StockItemNotFound(f'No stock record for book {book_id}') from None

    if on_hand < item.reserved:
        raise InvalidAdjustment(
            f'On hand cannot be lower than the reserved quantity ({item.reserved})'
        )

    difference = on_hand - item.on_hand
    item.on_hand = on_hand
    item.save(update_fields=['on_hand', 'updated_at'])
    _log(item, StockMovement.Kind.ADJUST, difference, user=user, note=note)
    return item
