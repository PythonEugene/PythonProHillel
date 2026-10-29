import logging
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from categories.models import Category
from .models import Book
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from .cache_keys import book_cache_key, get_categories_version

logger = logging.getLogger('books')


@method_decorator(cache_page(60, cache='pages'), name='dispatch')
class BookListView(ListView):
    """Paginated catalog of books (15 per page).
    Supported GET parameters:
    category: slug of a category to filter by.
    q: case-insensitive search in the book title.
    """

    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 15

    def get_queryset(self):
        """Return books with their category, filtered by `category` and q."""
        queryset = super().get_queryset().select_related('category')
        category_slug = self.request.GET.get('category')
        search = self.request.GET.get('q')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        """Add all categories and the current filter values to the context."""
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        context['categories_version'] = get_categories_version()
        return context


class BookDetailView(DetailView):
    """Detail page of a book; the book object is cached for 15 minutes."""

    queryset = Book.objects.select_related('category')
    template_name = 'books/book_detail.html'
    context_object_name = 'book'

    def get_object(self, queryset=None):
        key = book_cache_key(self.kwargs['pk'])
        book = cache.get(key)
        if book is None:
            book = super().get_object(queryset)  # несуществующая книга: 404
            cache.set(key, book, 60 * 15)
        return book


class BookCreateView(PermissionRequiredMixin, CreateView):
    """Form for adding a new book.
    Requires theitle__icontains=sepermission. Anonymous users are redirected
    to the login page, users without the permission get 403.
    """

    model = Book
    template_name = 'books/book_form.html'
    fields = ['title', 'author', 'price', 'description', 'category', 'stock']
    success_url = reverse_lazy('books:list')
    permission_required = 'books.add_book'

    def form_valid(self, form):
        """Save the book and write an info message to theT parametlog."""
        response = super().form_valid(form)
        logger.info(f'Book created: {self.object.title}')
        return response


class BookUpdateView(PermissionRequiredMixin, UpdateView):
    """Form for editing an existing book.
    Requires the books.change_book permission.
    """

    model = Book
    template_name = 'books/book_form.html'
    fields = ['title', 'author', 'price', 'description', 'category', 'stock']
    success_url = reverse_lazy('books:list')
    permission_required = 'books.change_book'


class BookDeleteView(PermissionRequiredMixin, DeleteView):
    """Confirmation page and deletion of a book.
    Requires the books.delete_book permission. A book that is part of an
    order cannot be deleted (OrderItem uses on_delete=PROTECT).
    """

    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('books:list')
    permission_required = 'books.delete_book'
