import factory
from stock.models import Reservation, ReservationItem, StockItem


class StockItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = StockItem

    book_id = factory.Sequence(lambda n: n + 1)
    title = factory.Sequence(lambda n: f'Book {n}')
    on_hand = 10
    reserved = 0


class ReservationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Reservation

    order_id = factory.Sequence(lambda n: n + 1)


class ReservationItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ReservationItem

    reservation = factory.SubFactory(ReservationFactory)
    book_id = factory.Sequence(lambda n: n + 1)
    quantity = 1
