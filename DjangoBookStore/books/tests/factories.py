import factory
from books.models import Book
from categories.models import Category

class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f'Category %d {n}')
    slug = factory.Sequence(lambda n: f'category-{n}')

class BookFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Book

    title = factory.Sequence(lambda n: f'Book {n}')
    category = factory.SubFactory(CategoryFactory)
    author = factory.Faker('name')
    stock = 5
    price = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)