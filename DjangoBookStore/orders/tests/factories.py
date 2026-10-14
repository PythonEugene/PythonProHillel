import factory
from orders.models import Order, OrderItem
from books.tests.factories import BookFactory

class OrderFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Order
    first_name = "Ivan"
    last_name = "Petrenko"
    email = factory.Sequence(lambda n: f"user{n}@test.com")
    phone_number = "+380501234567"
    address = "Kyiv, Khreshchatyk 1"
class OrderItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = OrderItem
    order = factory.SubFactory(OrderFactory)
    book = factory.SubFactory(BookFactory)
    price = 10
    quantity = 1