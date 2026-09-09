import stripe
from django.conf import settings
from django.core.mail import send_mail
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.http import HttpResponse
from books.models import Book
from .models import Order, OrderItem
from .cart import Cart
from .forms import OrderCreateForm

stripe.api_key = settings.STRIPE_SECRET_KEY


def cart_add(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.add(book=book, quantity=quantity)
    return redirect('orders:cart_detail')


def cart_detail(request):
    cart = Cart(request)
    context = {
        'cart': cart,
        'total_price': cart.get_total_price(),
    }
    return render(request, 'orders/cart_detail.html', context)


def cart_remove(request, book_id):
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('orders:cart_detail')


def order_create(request):
    cart = Cart(request)
    if not cart.cart:
        return redirect('orders:cart_detail')

    if request.method == 'POST':
        form = OrderCreateForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                order = form.save(commit=False)
                order.total_price = cart.get_total_price()
                if request.user.is_authenticated:
                    order.user = request.user
                order.save()

                for item in cart:
                    OrderItem.objects.create(
                        order=order,
                        book=item['book'],
                        quantity=item['quantity'],
                        price=item['price'],
                    )

            cart.clear()

            send_mail(
                subject=f'Замовлення №{order.id} створено',
                message=f'Дякуємо! Сума замовлення: {order.total_price} USD.',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[order.email],
                fail_silently=True,
            )

            return redirect('orders:order_payment', order_id=order.id)
    else:
        initial = {}
        if request.user.is_authenticated:
            user = request.user
            initial = {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
            }
        form = OrderCreateForm(initial=initial)

    context = {
        'form': form,
        'cart': cart,
        'total_price': cart.get_total_price(),
    }
    return render(request, 'orders/create_order.html', context)


def order_payment(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    line_items = [{
        'price_data': {
            'currency': 'usd',
            'product_data': {'name': item.book.title},
            'unit_amount': int(item.price * 100),
        },
        'quantity': item.quantity,
    } for item in order.items.all()]

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=['card'],
        line_items=line_items,
        mode='payment',
        success_url=request.build_absolute_uri(
            reverse('orders:order_success', args=[order.id])
        ),
        cancel_url=request.build_absolute_uri(
            reverse('orders:cart_detail')
        ),
        metadata={'order_id': str(order.id)},
    )

    order.stripe_checkout_id = checkout_session.id
    order.save(update_fields=['stripe_checkout_id'])

    return redirect(checkout_session.url, code=303)


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = Order.OrderStatus.PAID
    order.save(update_fields=['status'])
    return render(request, 'orders/success_order.html', {'order': order})

def stripe_webhook(request):
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        order_id = session['metadata']['order_id']
        with transaction.atomic():
            order = get_object_or_404(Order, id=order_id)
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=['status'])

    return HttpResponse(status=200)