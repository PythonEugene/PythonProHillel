from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from categories.models import Category
from .models import Book
import logging
from django.contrib.auth.mixins import PermissionRequiredMixin

logger = logging.getLogger('books')


class BookListView(ListView):
    model = Book
    template_name = 'books/book_list.html'
    context_object_name = 'books'
    paginate_by = 15

    def get_queryset(self):
        queryset = super().get_queryset().select_related('category')
        category_slug = self.request.GET.get('category')
        search = self.request.GET.get('q')

        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        if search:
            queryset = queryset.filter(title__icontains=search)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['categories'] = Category.objects.all()
        context['current_category'] = self.request.GET.get('category', '')
        context['search_query'] = self.request.GET.get('q', '')
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = 'books/book_detail.html'
    context_object_name = 'book'


class BookCreateView(CreateView):
    model = Book
    template_name = 'books/book_form.html'
    fields = ['title', 'author', 'price', 'description', 'category', 'stock']
    success_url = reverse_lazy('books:list')

    def form_valid(self, form):
        response = super().form_valid(form)
        logger.info(f'Book created: {self.object.title}')
        return response


class BookUpdateView(UpdateView):
    model = Book
    template_name = 'books/book_form.html'
    fields = ['title', 'author', 'price', 'description', 'category', 'stock']
    success_url = reverse_lazy('books:list')


class BookDeleteView(DeleteView, PermissionRequiredMixin):
    model = Book
    template_name = 'books/book_confirm_delete.html'
    success_url = reverse_lazy('books:list')
    permission_required = 'books.delete_book'






