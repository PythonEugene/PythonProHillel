import django_filters
from django.conf import settings
from django.db.models import F
from stock.models import StockItem


class StockItemFilter(django_filters.FilterSet):
    low_stock = django_filters.BooleanFilter(method='filter_low_stock')

    class Meta:
        model = StockItem
        fields = []

    def filter_low_stock(self, queryset, name, value):
        """?low_stock=true keeps books whose available quantity is at or below the threshold."""
        low = queryset.annotate(free=F('on_hand') - F('reserved')).filter(
            free__lte=settings.LOW_STOCK_THRESHOLD
        )
        if value:
            return low
        return queryset.exclude(pk__in=low.values('pk'))
