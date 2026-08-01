from django.contrib import admin
from .models import Book


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'price', 'stock', 'category',)
    search_fields = ('author', 'category')
    search_fields = ('title', 'author', 'description')


