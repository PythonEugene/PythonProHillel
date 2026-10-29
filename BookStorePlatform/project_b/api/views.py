from drf_spectacular.utils import extend_schema
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from stock import services
from stock.models import Reservation, StockItem
from .filters import StockItemFilter
from .permissions import ActionPermissionMixin
from .serializers import (
    ReceiveSerializer,
    ReservationCreateSerializer,
    ReservationSerializer,
    StockItemSerializer,
)


class StockViewSet(
    ActionPermissionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Stock levels of books. Books are identified by their id in ProjectA."""

    queryset = StockItem.objects.all()
    serializer_class = StockItemSerializer
    lookup_field = 'book_id'
    lookup_url_kwarg = 'book_id'
    lookup_value_regex = r'\d+'
    filterset_class = StockItemFilter
    search_fields = ['title']
    ordering_fields = ['book_id', 'on_hand', 'reserved']
    permission_by_action = {
        'list': 'view_stockitem',
        'retrieve': 'view_stockitem',
        'receive': 'adjust_stock',
    }

    @extend_schema(request=ReceiveSerializer, responses=StockItemSerializer)
    @action(detail=True, methods=['post'])
    def receive(self, request, book_id=None):
        """Register a delivery of books to the warehouse."""
        serializer = ReceiveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item = services.receive(
            book_id=int(book_id), user=request.user, **serializer.validated_data
        )
        return Response(StockItemSerializer(item).data)


class ReservationViewSet(
    ActionPermissionMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    viewsets.GenericViewSet,
):
    """Reservations of books for orders. Reservations are identified by the order id."""

    queryset = Reservation.objects.prefetch_related('items')
    serializer_class = ReservationSerializer
    lookup_field = 'order_id'
    lookup_value_regex = r'\d+'
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'order_id']
    permission_by_action = {
        'list': 'view_reservation',
        'retrieve': 'view_reservation',
        'create': 'reserve_stock',
        'confirm': 'reserve_stock',
        'release': 'reserve_stock',
    }

    @extend_schema(
        request=ReservationCreateSerializer,
        responses={201: ReservationSerializer},
    )
    def create(self, request):
        """Reserve books for an order. Repeating the request is safe (idempotent)."""
        serializer = ReservationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reservation = services.reserve(
            order_id=serializer.validated_data['order_id'],
            items=serializer.validated_data['items'],
            user=request.user,
        )
        return Response(ReservationSerializer(reservation).data, status=status.HTTP_201_CREATED)

    @extend_schema(request=None, responses=ReservationSerializer)
    @action(detail=True, methods=['post'])
    def confirm(self, request, order_id=None):
        """The order is paid: books leave the warehouse."""
        reservation = services.confirm(int(order_id), user=request.user)
        return Response(ReservationSerializer(reservation).data)

    @extend_schema(request=None, responses=ReservationSerializer)
    @action(detail=True, methods=['post'])
    def release(self, request, order_id=None):
        """The order is canceled: reserved books become available again."""
        reservation = services.release(int(order_id), user=request.user)
        return Response(ReservationSerializer(reservation).data)
