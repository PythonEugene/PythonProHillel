import django_filters

from books.models import Book


class BookFilter(django_filters.FilterSet):
    price_min = django_filters.NumberFilter(field_name='price', lookup_expr='gte')
    price_max = django_filters.NumberFilter(field_name='price', lookup_expr='lte')
    category = django_filters.CharFilter(field_name='category__slug')
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')

    class Meta:
        model = Book
        fields = ['author']

    def filter_in_stock(self, queryset, name, value):
        """?in_stock=true -> only available books, false -> sold out."""
        return queryset.filter(stock__gt=0) if value else queryset.filter(stock=0)