from django.shortcuts import render
from books.models import Book
from django.http import HttpResponse
from categories.models import Category
from django.db.models import Count, Avg, Q

def test_orm(request):
    cheap_books = Book.objects.filter(price__lt=500)
    print("Cheap Books:", cheap_books)


