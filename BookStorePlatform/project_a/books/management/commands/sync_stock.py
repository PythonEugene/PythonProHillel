from django.core.management.base import BaseCommand
from books.models import Book
from services.warehouse_client import WarehouseClient


class Command(BaseCommand):
    help = 'Load initial stock of all books into the warehouse'

    def add_arguments(self, parser):
        parser.add_argument('--quantity', type=int, default=10)

    def handle(self, *args, **opts):
        client = WarehouseClient()
        for book in Book.objects.all():
            client.receive(book.id, opts['quantity'], book.title)