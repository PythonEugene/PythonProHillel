from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('cart/add/<int:book_id>/', views.cart_add, name='cart_add'),
    path('cart/remove/<int:book_id>/', views.cart_remove, name='cart_remove'),
    path('cart/', views.cart_detail, name='cart_detail'),
    path('create/', views.order_create, name='order_create'),
    path('<int:order_id>/pay/', views.order_payment, name='order_payment'),
    path('<int:order_id>/success/', views.order_success, name='order_success'),
    path('webhook/', views.stripe_webhook, name='stripe_webhook'),
]