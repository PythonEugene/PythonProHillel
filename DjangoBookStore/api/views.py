from django.db.models import Count
from rest_framework import viewsets

from books.models import Book
from categories.models import Category
from .filters import BookFilter
from .permissions import IsAdminOrReadOnly
from .serializers import (
    BookSerializer,
    CategorySerializer,
    CategoryDetailSerializer,
)
from rest_framework import generics
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import RegisterSerializer, UserSerializer
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from orders.models import Order
from .permissions import IsOwnerOrReadOnly
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    OrderUpdateSerializer,
)
from drf_spectacular.utils import extend_schema
from orders.cart import Cart
from .serializers import (
    CartSerializer,
    CartAddSerializer,
    CartRemoveSerializer,
)


class BookViewSet(viewsets.ModelViewSet):
    """CRUD for books. Anyone can read, only staff can change."""

    queryset = Book.objects.select_related('category').order_by('id')
    serializer_class = BookSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_class = BookFilter
    search_fields = ['title', 'author']
    ordering_fields = ['price', 'title', 'stock']


class CategoryViewSet(viewsets.ModelViewSet):
    """CRUD for categories. Detail view includes the books of the category."""

    queryset = Category.objects.annotate(books_count=Count('books')).order_by('name')
    permission_classes = [IsAdminOrReadOnly]
    search_fields = ['name']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return CategoryDetailSerializer
        return CategorySerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action == 'retrieve':
            queryset = queryset.prefetch_related('books')
        return queryset


class RegisterView(generics.CreateAPIView):
    """Create a new user account."""

    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]


class MeView(generics.RetrieveAPIView):
    """Profile of the current user."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user


class OrderViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """Orders of the current user (staff sees all orders).

    Orders cannot be deleted. Contact data can be edited and the order can be
    canceled only by its owner and only while it is PENDING.
    """

    permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'head', 'options']
    filterset_fields = ['status']
    ordering_fields = ['created_at', 'total_price']

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False):  # для генерации документации
            return Order.objects.none()
        queryset = (
            Order.objects.select_related('user')
            .prefetch_related('items__book')
            .order_by('-created_at')
        )
        if self.request.user.is_staff:
            return queryset
        return queryset.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        if self.action in ('update', 'partial_update'):
            return OrderUpdateSerializer
        return OrderSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        data = OrderSerializer(order, context=self.get_serializer_context()).data
        return Response(data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        if self.get_object().status != Order.OrderStatus.PENDING:
            raise ValidationError({'detail': 'Only pending orders can be changed.'})
        return super().update(request, *args, **kwargs)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel a pending order."""
        order = self.get_object()
        if order.status != Order.OrderStatus.PENDING:
            raise ValidationError({'detail': 'Only pending orders can be canceled.'})
        order.status = Order.OrderStatus.CANCELED
        order.save(update_fields=['status'])
        return Response(OrderSerializer(order).data)


class CartViewSet(viewsets.ViewSet):
    """Session cart. Works for anonymous users too (like the website)."""

    permission_classes = [AllowAny]

    def _cart_response(self, request, status_code=status.HTTP_200_OK):
        cart = Cart(request)
        data = CartSerializer(
            {
                'items': list(cart),
                'total_items': len(cart),
                'total_price': cart.get_total_price(),
            }
        ).data
        return Response(data, status=status_code)

    @extend_schema(responses=CartSerializer)
    def list(self, request):
        """Show the cart."""
        return self._cart_response(request)

    @extend_schema(request=CartAddSerializer, responses=CartSerializer)
    @action(detail=False, methods=['post'])
    def add(self, request):
        """Add a book (or set its quantity with override=true)."""
        serializer = CartAddSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        book = serializer.validated_data['book']
        quantity = serializer.validated_data['quantity']
        override = serializer.validated_data['override']

        cart = Cart(request)
        current = cart.cart.get(str(book.id), {}).get('quantity', 0)
        new_quantity = quantity if override else current + quantity
        if new_quantity > book.stock:
            raise ValidationError({'quantity': f'Only {book.stock} in stock.'})

        cart.add(book=book, quantity=quantity, override_quantity=override)
        return self._cart_response(request, status.HTTP_201_CREATED)

    @extend_schema(request=CartRemoveSerializer, responses=CartSerializer)
    @action(detail=False, methods=['post'])
    def remove(self, request):
        """Remove a book from the cart."""
        serializer = CartRemoveSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        Cart(request).remove(serializer.validated_data['book'])
        return self._cart_response(request)

    @extend_schema(request=None, responses=CartSerializer)
    @action(detail=False, methods=['post'])
    def clear(self, request):
        """Remove everything from the cart."""
        Cart(request).clear()
        return self._cart_response(request)
