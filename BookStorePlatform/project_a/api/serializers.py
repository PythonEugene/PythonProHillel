from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from users.models import CustomUser
from books.models import Book
from categories.models import Category
from decimal import Decimal
from django.db import transaction
from orders.models import Order, OrderItem


class CategoryShortSerializer(serializers.ModelSerializer):
    """Compact category, used inside a book."""

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug']


class BookShortSerializer(serializers.ModelSerializer):
    """Compact book, used inside a category."""

    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'price']


class BookSerializer(serializers.ModelSerializer):
    category = CategoryShortSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.all(), source='category', write_only=True
    )

    class Meta:
        model = Book
        fields = [
            'id',
            'title',
            'author',
            'price',
            'description',
            'stock',
            'category',
            'category_id',
        ]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError('Price must be greater than zero.')
        return value


class CategorySerializer(serializers.ModelSerializer):
    books_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'books_count']


class CategoryDetailSerializer(CategorySerializer):
    """Single category with the list of its books."""

    books = BookShortSerializer(many=True, read_only=True)

    class Meta(CategorySerializer.Meta):
        fields = CategorySerializer.Meta.fields + ['books']


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])

    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'first_name': {'required': True, 'allow_blank': False},
            'phone_number': {'required': True, 'allow_blank': False},
        }

    def create(self, validated_data):
        # create_user хеширует пароль, обычный create() сохранил бы его открытым текстом
        return CustomUser.objects.create_user(**validated_data)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'email', 'phone_number', 'first_name', 'last_name', 'date_joined']
        read_only_fields = fields


class OrderItemSerializer(serializers.ModelSerializer):
    """Order line for reading: nested book, price and line total."""

    book = BookShortSerializer(read_only=True)
    total = serializers.DecimalField(
        max_digits=12, decimal_places=2, source='get_total', read_only=True
    )

    class Meta:
        model = OrderItem
        fields = ['id', 'book', 'price', 'quantity', 'total']


class OrderSerializer(serializers.ModelSerializer):
    """Order for reading, with nested items."""

    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = [
            'id',
            'first_name',
            'last_name',
            'email',
            'phone_number',
            'address',
            'status',
            'total_price',
            'created_at',
            'items',
        ]
        read_only_fields = ['status', 'total_price', 'created_at']


class OrderItemInputSerializer(serializers.Serializer):
    """One line of a new order: book id and quantity."""

    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book')
    quantity = serializers.IntegerField(min_value=1, max_value=100)


class OrderCreateSerializer(serializers.ModelSerializer):
    """Input for creating an order. Prices are taken from the database."""

    items = OrderItemInputSerializer(many=True, allow_empty=False)

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address', 'items']

    def validate_items(self, items):
        seen = set()
        for item in items:
            book = item['book']
            if book.id in seen:
                raise serializers.ValidationError(f'Book {book.id} is listed more than once.')
            seen.add(book.id)
            if item['quantity'] > book.stock:
                raise serializers.ValidationError(
                    f'Not enough stock for "{book.title}" (available: {book.stock}).'
                )
        return items

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop('items')
        order = Order.objects.create(user=self.context['request'].user, **validated_data)
        total = Decimal('0')
        for item in items:
            book = item['book']
            OrderItem.objects.create(
                order=order, book=book, price=book.price, quantity=item['quantity']
            )
            total += book.price * item['quantity']
        order.total_price = total
        order.save(update_fields=['total_price'])
        return order


class OrderUpdateSerializer(serializers.ModelSerializer):
    """Only contact and delivery data can be edited."""

    class Meta:
        model = Order
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'address']


class CartItemSerializer(serializers.Serializer):
    """One cart line (read only)."""

    book = BookShortSerializer()
    quantity = serializers.IntegerField()
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class CartSerializer(serializers.Serializer):
    """Whole cart (read only)."""

    items = CartItemSerializer(many=True)
    total_items = serializers.IntegerField()
    total_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class CartAddSerializer(serializers.Serializer):
    """Input for adding a book to the cart."""

    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book')
    quantity = serializers.IntegerField(min_value=1, max_value=100, default=1)
    override = serializers.BooleanField(default=False)  # true: задать количество, а не прибавить


class CartRemoveSerializer(serializers.Serializer):
    """Input for removing a book from the cart."""

    book_id = serializers.PrimaryKeyRelatedField(queryset=Book.objects.all(), source='book')
