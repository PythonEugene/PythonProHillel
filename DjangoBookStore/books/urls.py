from django.urls import path
from . import views

app_name = 'books'

urlpatterns = [
    path('',views.BookListView.as_view(),name='list'),
    path('<int:pk>/',views.BookDetailView.as_view(),name='detail'),
    path('add/',views.BookCreateView.as_view(),name='add'),
    path('<int:pk>/edit/',views.BookUpdateView.as_view(),name='edit'),
    path('<int:pk>/delete/',views.BookDeleteView.as_view(),name='delete'),
]