from django.urls import path
from . import views, async_views

app_name = 'books'

urlpatterns = [
    path('',views.BookListView.as_view(),name='list'),
    path('<int:pk>/',views.BookDetailView.as_view(),name='detail'),
    path('add/',views.BookCreateView.as_view(),name='add'),
    path('<int:pk>/edit/',views.BookUpdateView.as_view(),name='edit'),
    path('<int:pk>/delete/',views.BookDeleteView.as_view(),name='delete'),
    path("api/books/", async_views.books_api, name="books_api"),
    path("api/books/<int:pk>/",async_views.book_detail_api, name="book_detail_api"),
    path("api/stats/", async_views.stats_api, name="api_stats"),
]