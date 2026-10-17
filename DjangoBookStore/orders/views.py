import logging
import stripe
from django.conf import settings
from .tasks import send_order_confirmation
from django.db import transaction
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from books.models import Book
from .cart import Cart
from .forms import OrderCreateForm
from .models import Order, OrderItem


logger = logging.getLogger(__name__)

stripe.api_key = settings.STRIPE_SECRET_KEY
def cart_add(request, book_id):
    """Add a book to the session cart.
    Only POST requests change the cart; a GET request just redirects.
    POST parameter `quantity` (default 1) is added to the current quantity.

    Args:
        request: the HTTP request.
        book_id: id of the book to add.
        Returns 404 if it does not exist.

    Returns:
        Redirect to the cart page.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart.add(book=book, quantity=quantity)
    return redirect('orders:cart_detail')


def cart_detail(request):
    """Show the cart contents and the total price.
    Returns:
    Rendered orders/cart_detail.html.
    """
    cart = Cart(request)
    context = {
        'cart': cart,
        'total_price': cart.get_total_price(),
    }
    return render(request, 'orders/cart_detail.html', context)


def cart_remove(request, book_id):
    """Remove a book from the session cart.
    Args:
        request: the HTTP request.
        book_id: id of the book to remove. Returns 404 if it does not exist.

    Returns:
        Redirect to the cart page.
    """
    cart = Cart(request)
    book = get_object_or_404(Book, id=book_id)
    cart.remove(book)
    return redirect('orders:cart_detail')


def order_create(request):
    """Create an order from the cart.
    GET shows the checkout form (prefilled for authenticated users).
    POST validates the form and, inside one transaction, creates the Order
    and an OrderItem for every cart line. After that the cart is cleared,
    a confirmation email is sent and the user is redirected to payment.
    An empty cart redirects to the cart page.

    Returns:
        Renderedst.

    Returns:
        Redirect t or a redirect to the cart page
        (empty cart) or to the payment page (order created).
    """
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
            send_order_confirmation.delay(order.id)

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
    """Create a Stripe Checkout session for the order and redirect to it.
    The session id is saved inst)
    book = get_object_or_404 so the payment
    can be verified later. Stripe redirects back to order_success afterpayment, or to the cart page if the user cancels.

    Args:
        request: the HTTP request.
        order_id: id of the order to pay. Returns 404 if it does not exist.

    Returns:
        HTTP 303 redirect to the Stripe payment page.
    """
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

    return HttpResponseRedirect(checkout_session.url, status=303)


def order_success(request, order_id):
    """Show the "payment successful" page.
    The order status is changed to PAID only if the order is still PENDING
    and Stripe confirms the payment.

    Args:
        request: the HTTP request.
        order_id: id of the order. Returns 404 if it does not exist.

    Returns:
        Renderedcart': cart,
        'total_price
    """
    order = get_object_or_404(Order, id=order_id)

    if order.status == Order.OrderStatus.PENDING and order.stripe_checkout_id:
        session = stripe.checkout.Session.retrieve(order.stripe_checkout_id)
        if session.payment_status == 'paid':
            order.status = Order.OrderStatus.PAID
            order.save(update_fields=['status'])

    return render(request, 'orders/success_order.html', {'order': order})


@csrf_exempt
@require_POST
def stripe_webhook(request):
    """Receive Stripe notifications and mark the order as paid.
    The request signature is verified with the webhook secret. Only the
    checkout.session.completed event is handled; repeated deliveries are
    safe because only PENDING orders are updated.

    Returns:
        HTTP 400 if the payload or signature is invalid, otherwise HTTP 200
        (also when the order is unknown, to stop Stripe from retrying).
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except (ValueError, stripe.SignatureVerificationError):
        return HttpResponse(status=400)

    if event['type'] == 'checkout.session.completed':
        order_id = event['data']['object']['metadata']['order_id']
        with transaction.atomic():
            order = Order.objects.select_for_update().filter(id=order_id).first()
            if order is None:
                logger.warning('Webhook for unknown order %s', order_id)
            elif order.status == Order.OrderStatus.PENDING:
                order.status = Order.OrderStatus.PAID
                order.save(update_fields=['status'])

    return HttpResponse(status=200)