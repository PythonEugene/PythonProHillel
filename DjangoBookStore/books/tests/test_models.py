import pytest
from books.tests.factories import BookFactory, CategoryFactory
from django.core.exceptions import ValidationError

@pytest.mark.django_db
def test_book_str():
    book = BookFactory(title="Python for beginers")
    assert str(book) == "Python for beginers"


@pytest.mark.django_db
def test_book_default_stock_is_zero():
    book = BookFactory(stock=0)
    assert book.stock == 0


@pytest.mark.django_db
def test_book_negative_stock_is_invalid():
    book = BookFactory.build(stock=-1)
    with pytest.raises(ValidationError):
        book.full_clean()


@pytest.mark.django_db
def test_category_books_related_name():
    category = CategoryFactory()
    BookFactory.create_batch(3, category=category)
    assert category.books.count() == 3