from decimal import Decimal
from django.conf import settings
from books.models import Book


class Cart:
    def __init__(self, request):
        self.request = request
        self.session = request.session
        cart = self.session.get(settings.CART_SESSION_ID)
        if not cart:
            cart = self.session[settings.CART_SESSION_ID] = {}
        self.cart = cart

    def add(self, book: Book, quantity=1, override_quantity=False):
        book_id = str(book.id)
        if book_id not in self.cart:
            self.cart[book_id] = {'quantity': 0, 'price': str(book.price)}

        if quantity <= 0:
            quantity = 1

        if override_quantity:
            self.cart[book_id]['quantity'] = quantity
        else:
            self.cart[book_id]['quantity'] += quantity

        self.save()

    def save(self):
        self.session.modified = True

    def remove(self, book: Book):
        book_id = str(book.id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def clear(self):
        self.session[settings.CART_SESSION_ID] = {}
        self.save()

    def __iter__(self):
        books = Book.objects.filter(id__in=self.cart.keys())
        books_map = {str(b.id): b for b in books}
        for book_id, item in self.cart.items():
            item = item.copy()
            item['book'] = books_map[book_id]
            item['total_price'] = Decimal(item['price']) * item['quantity']
            yield item

    def len(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        return sum(Decimal(i['price']) * i['quantity'] for i in self.cart.values())