from django.contrib import admin

from .models import Reservation, ReservationItem, StockItem, StockMovement


class ReservationItemInline(admin.TabularInline):
    model = ReservationItem
    extra = 0


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'title', 'on_hand', 'reserved', 'available')
    search_fields = ('title', 'book_id')


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('order_id', 'status', 'expires_at', 'created_at')
    list_filter = ('status',)
    inlines = [ReservationItemInline]


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'stock_item', 'kind', 'quantity', 'order_id', 'created_by')
    list_filter = ('kind',)

    def has_add_permission(self, request):
        return False  # журнал только для чтения

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
