import csv

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Count, Sum
from django.utils import timezone

from .models import Order, OrderItem


@shared_task(autoretry_for=(OSError,), retry_backoff=True, max_retries=3)
def send_order_confirmation(order_id):
    """Send the order confirmation email (retried if the mail server fails)."""
    order = Order.objects.get(id=order_id)
    send_mail(
        subject=f'Замовлення №{order.id} створено',
        message=f'Дякуємо! Сума замовлення: {order.total_price} USD.',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
    )


@shared_task
def generate_daily_report():
    """Write a CSV report of today's paid orders and return its path."""
    today = timezone.localdate()
    paid = Order.objects.filter(status=Order.OrderStatus.PAID, created_at__date=today)
    totals = paid.aggregate(orders=Count('id'), revenue=Sum('total_price'))
    top_books = (
        OrderItem.objects.filter(order__in=paid)
        .values('book__title')
        .annotate(sold=Sum('quantity'))
        .order_by('-sold')[:5]
    )

    settings.REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = settings.REPORTS_DIR / f'sales_{today}.csv'
    with path.open('w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(['date', 'paid_orders', 'revenue'])
        writer.writerow([today, totals['orders'], totals['revenue'] or 0])
        writer.writerow([])
        writer.writerow(['top_books', 'sold'])
        for row in top_books:
            writer.writerow([row['book__title'], row['sold']])
    return str(path)
