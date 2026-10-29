from rest_framework import serializers
from stock.models import Reservation, ReservationItem, StockItem


class StockItemSerializer(serializers.ModelSerializer):
    """Stock level of a book (read only)."""

    available = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockItem
        fields = ['book_id', 'title', 'on_hand', 'reserved', 'available', 'updated_at']
        read_only_fields = fields


class ReceiveSerializer(serializers.Serializer):
    """Input for registering a delivery of books."""

    quantity = serializers.IntegerField(min_value=1, max_value=100000)
    title = serializers.CharField(max_length=200, required=False, allow_blank=True, default='')
    note = serializers.CharField(max_length=255, required=False, allow_blank=True, default='')


class ReservationItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReservationItem
        fields = ['book_id', 'quantity']
        read_only_fields = fields


class ReservationSerializer(serializers.ModelSerializer):
    """Reservation with its lines (read only)."""

    items = ReservationItemSerializer(many=True, read_only=True)

    class Meta:
        model = Reservation
        fields = ['order_id', 'status', 'expires_at', 'created_at', 'items']
        read_only_fields = fields


class ReservationItemInputSerializer(serializers.Serializer):
    book_id = serializers.IntegerField(min_value=1)
    quantity = serializers.IntegerField(min_value=1, max_value=1000)


class ReservationCreateSerializer(serializers.Serializer):
    """Input for creating a reservation for an order."""

    order_id = serializers.IntegerField(min_value=1)
    items = ReservationItemInputSerializer(many=True, allow_empty=False)
