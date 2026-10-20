import random
from django.core.management.base import BaseCommand
from books.models import Book
from categories.models import Category

DEFAULT_CATEGORIES = [
    ('Programming', 'programming'),
    ('Databases', 'databases'),
    ('Web Development', 'web-development'),
]

ADJECTIVES = [
    'Advanced',
    'Mastering',
    'Learning',
    'Python for',
    'Practical',
    'Modern',
    'Clean',
    'Ultimate',
    'Deep Dive into',
    'Beginning',
]

NOUNS = [
    'Algorithms',
    'Web Development',
    'Artificial Intelligence',
    'Data Science',
    'Django Framework',
    'Software Architecture',
    'Databases',
    'API Design',
    'Cybersecurity',
    'Backend Systems',
]

AUTHORS = [
    'Mark Lutz',
    'Luciano Ramalho',
    'Robert Martin',
    'John Smith',
    'Alice Johnson',
    'Michael Brown',
    'David Beazley',
]


class Command(BaseCommand):
    help = 'Creates random books (100 by default). Creates default categories if there are none.'

    def add_arguments(self, parser):
        parser.add_argument(
            'total', nargs='?', type=int, default=100, help='Number of books to create'
        )

    def handle(self, *args, **options):
        total = options['total']

        if not Category.objects.exists():
            for name, slug in DEFAULT_CATEGORIES:
                Category.objects.get_or_create(slug=slug, defaults={'name': name})
            self.stdout.write('No categories found, created default ones.')

        categories = list(Category.objects.all())
        books_to_create = []

        for i in range(1, total + 1):
            title = f'{random.choice(ADJECTIVES)} {random.choice(NOUNS)} #{i}'
            description = f'Randomly generated description for the book "{title}".'
            books_to_create.append(
                Book(
                    title=title,
                    author=random.choice(AUTHORS),
                    price=round(random.uniform(500, 3000), 2),
                    description=description,
                    stock=random.randint(0, 50),
                    category=random.choice(categories),
                )
            )
        Book.objects.bulk_create(books_to_create)

        self.stdout.write(self.style.SUCCESS(f'Successfully created {total} random books!'))
