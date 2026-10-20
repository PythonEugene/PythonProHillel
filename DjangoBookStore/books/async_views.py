from django.http import JsonResponse, Http404
from .models import Book
from categories.models import Category


async def books_api(request):
    qs = Book.objects.select_related("category").order_by("-id")[:20]
    books = [{"id": b.id, "title": b.title, "category": b.category.name} async for b in qs]
    return JsonResponse({"books": books})


async def book_detail_api(request, pk):
    try:
        b = await Book.objects.select_related("category").aget(pk=pk)
    except Book.DoesNotExist:
        raise Http404
    return JsonResponse({"id": b.id, "title": b.title, "category": b.category.name})


async def stats_api(request):
    return JsonResponse(
        {
            "books": await Book.objects.acount(),
            "categories": await Category.objects.acount(),
        }
    )
