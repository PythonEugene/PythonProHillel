import csv
from datetime import timedelta
import pytest
from django.contrib.sessions.models import Session
from django.core import mail
from django.utils import timezone
from orders.models import Order
from orders.tasks import generate_daily_report, send_order_confirmation
from orders.tests.factories import OrderFactory, OrderItemFactory
from users.tasks import clear_expired_sessions

pytestmark = pytest.mark.django_db


def test_send_order_confirmation_sends_email():
    order = OrderFactory(email='buyer@test.com', total_price=25)
    send_order_confirmation.delay(order.id)
    assert len(mail.outbox) == 1
    assert mail.outbox[0].to == ['buyer@test.com']
    assert str(order.id) in mail.outbox[0].subject


def test_daily_report_counts_only_paid_orders(settings, tmp_path):
    settings.REPORTS_DIR = tmp_path
    paid = OrderFactory(status=Order.OrderStatus.PAID, total_price=30)
    OrderItemFactory(order=paid, price=15, quantity=2)
    OrderFactory(status=Order.OrderStatus.PENDING, total_price=99)

    path = generate_daily_report.delay().get()

    rows = list(csv.reader(open(path, encoding='utf-8')))
    assert rows[1][1:] == ['1', '30']
    assert rows[-1][1] == '2'  # sold quantity of the top book

def test_clear_expired_sessions_removes_only_expired():
    now = timezone.now()
    Session.objects.create(session_key='old', session_data='x', expire_date=now - timedelta(days=1))
    Session.objects.create(session_key='new', session_data='x', expire_date=now + timedelta(days=1))
    clear_expired_sessions.delay()
    assert list(Session.objects.values_list('session_key', flat=True)) == ['new']