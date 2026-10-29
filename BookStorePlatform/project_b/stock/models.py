from datetime import timedelta
from django.conf import settings
from django.db import models
from django.db.models import F, Q
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def default_expiry():
    """Moment when a new reservation expires: now + RESERVATION_TTL_MINUTES."""
    return timezone.now() + timedelta(minutes=settings.RESERVATION_TTL_MINUTES)


class StockItem(models.Model):
    """Stock level of one book.
    The book itself lives in ProjectA, the warehouse knows it only by `book_id`.
    """

    book_id = models.PositiveIntegerField(unique=True, verbose_name=_('Book ID'))
    title = models.CharField(max_length=200, blank=True, verbose_name=_('Title'))
    on_hand = models.PositiveIntegerField(default=0, verbose_name=_('On hand'))
    reserved = models.PositiveIntegerField(default=0, verbose_name=_('Reserved'))
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['book_id']
        verbose_name = _('Stock item')
        verbose_name_plural = _('Stock items')
        constraints = [
            models.CheckConstraint(
                condition=Q(reserved__lte=F('on_hand')),
                name='stock_reserved_lte_on_hand',
            ),
        ]
        permissions = [
            ('reserve_stock', 'Can reserve, confirm and release stock'),
            ('adjust_stock', 'Can receive and adjust stock'),
            ('view_reports', 'Can view warehouse reports'),
        ]

    def __str__(self):
        return f'#{self.book_id} {self.title}'.strip()

    @property
    def available(self):
        """Books that can still be reserved."""
        return self.on_hand - self.reserved

    @property
    def is_low(self):
        """True when the available quantity is at or below the configured threshold."""
        return self.available <= settings.LOW_STOCK_THRESHOLD


class Reservation(models.Model):
    """Books held for one order of ProjectA."""

    class Status(models.TextChoices):
        RESERVED = 'RESERVED', _('Reserved')
        CONFIRMED = 'CONFIRMED', _('Confirmed')
        RELEASED = 'RELEASED', _('Released')
        EXPIRED = 'EXPIRED', _('Expired')

    order_id = models.PositiveIntegerField(unique=True, verbose_name=_('Order ID'))
    status = models.CharField(
        max_length=10,
        choices=Status.choices,
        default=Status.RESERVED,
        verbose_name=_('Status'),
    )
    expires_at = models.DateTimeField(default=default_expiry, verbose_name=_('Expires at'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Reservation')
        verbose_name_plural = _('Reservations')

    def __str__(self):
        return f'Reservation for order {self.order_id} ({self.status})'

    @property
    def is_expired(self):
        """An unpaid reservation whose time is over."""
        return self.status == self.Status.RESERVED and self.expires_at <= timezone.now()


class ReservationItem(models.Model):
    """One line of a reservation."""

    reservation = models.ForeignKey(Reservation, on_delete=models.CASCADE, related_name='items')
    book_id = models.PositiveIntegerField()
    quantity = models.PositiveIntegerField()

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['reservation', 'book_id'], name='unique_book_per_reservation'
            ),
            models.CheckConstraint(condition=Q(quantity__gte=1), name='reservation_quantity_gte_1'),
        ]

    def __str__(self):
        return f'{self.quantity} x book {self.book_id}'


class StockMovement(models.Model):
    """Journal of every change of stock (who, what, why)."""

    class Kind(models.TextChoices):
        RECEIVE = 'RECEIVE', _('Receive')
        RESERVE = 'RESERVE', _('Reserve')
        RELEASE = 'RELEASE', _('Release')
        SHIP = 'SHIP', _('Ship')
        ADJUST = 'ADJUST', _('Adjust')

    stock_item = models.ForeignKey(StockItem, on_delete=models.CASCADE, related_name='movements')
    kind = models.CharField(max_length=10, choices=Kind.choices)
    quantity = models.IntegerField()
    order_id = models.PositiveIntegerField(null=True, blank=True)
    note = models.CharField(max_length=255, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at', '-id']
        verbose_name = _('Stock movement')
        verbose_name_plural = _('Stock movements')

    def __str__(self):
        return f'{self.kind} {self.quantity} (book {self.stock_item.book_id})'
