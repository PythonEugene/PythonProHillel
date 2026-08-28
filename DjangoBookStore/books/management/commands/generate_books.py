import random
from django.core.management.base import BaseCommand
from books.models import Book
from categories.models import Category


class Command(BaseCommand):
    help = 'Creates 100 random books with English titles and categories'

    def add_arguments(self, parser):
        parser.add_argument(
            'total',
            nargs='?',
            type=int,
            default=10,
            help='Number of books to create'

        )

    def handle(self, *args, **options):
        categories = list(Category.objects.all())

        if not categories:
            self.stdout.write(self.style.ERROR('Please create at least one category in the database first!'))
            return

        adjectives = ['Advanced', 'Mastering', 'Learning', 'Python for', 'Practical', 'Modern', 'Clean', 'Ultimate',
                      'Deep Dive into', 'Beginning']
        nouns = ['Algorithms', 'Web Development', 'Artificial Intelligence', 'Data Science', 'Django Framework',
                 'Software Architecture', 'Databases', 'API Design', 'Cybersecurity', 'Backend Systems']
        authors = ['Mark Lutz', 'Luciano Ramalho', 'Robert Martin', 'John Smith', 'Alice Johnson', 'Michael Brown',
                   'David Beazley']

        books_to_create = []

        for i in range(1, 101):
            title = f"{random.choice(adjectives)} {random.choice(nouns)} #{i}"
            author = random.choice(authors)
            price = round(random.uniform(500, 3000), 2)
            stock = random.randint(0, 50)
            random_category = random.choice(categories)

            book = Book(
                title=title,
                author=author,
                price=price,
                description=f'This is a randomly generated description for the book "{title}".',
                stock=stock,
                category=random_category
            )
            books_to_create.append(book)


        Book.objects.bulk_create(books_to_create)

        self.stdout.write(self.style.SUCCESS('Successfully created 100 random books in English!'))