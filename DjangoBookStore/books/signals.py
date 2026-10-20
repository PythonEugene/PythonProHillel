from django.core.cache import cache, caches
from django.db import transaction
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
from categories.models import Category
from .cache_keys import book_cache_key, bump_categories_version
from .models import Book


@receiver([post_save, post_delete], sender=Book)
def invalidate_book_cache(sender, instance, **kwargs):
    """A book changed: drop its detail cache and all cached catalog pages."""

    def invalidate():
        cache.delete(book_cache_key(instance.pk))
        caches['pages'].clear()

    # on_commit: сбрасываем кеш только после того, как изменение записано в БД
    transaction.on_commit(invalidate)


@receiver([post_save, post_delete], sender=Category)
def invalidate_category_cache(sender, instance, **kwargs):
    """A category changed: refresh the categories fragment, pages and its books."""
    book_ids = list(instance.books.values_list('id', flat=True))

    def invalidate():
        cache.delete_many([book_cache_key(pk) for pk in book_ids])
        bump_categories_version()
        caches['pages'].clear()

    transaction.on_commit(invalidate)
