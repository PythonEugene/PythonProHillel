import time
from django.core.cache import cache

CATEGORIES_VERSION_KEY = 'categories_version'


def book_cache_key(pk):
    """Cache key of the book detail object."""
    return f'book:{pk}'


def get_categories_version():
    """Version number of the categories fragment (created on first use)."""
    return cache.get_or_set(CATEGORIES_VERSION_KEY, time.time_ns, None)


def bump_categories_version():
    """Change the version, so the old categories fragment is never used again."""
    cache.set(CATEGORIES_VERSION_KEY, time.time_ns(), None)