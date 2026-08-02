from django.contrib import admin
from django.db.models import Sum, Count
from django.http import HttpResponse
import csv
from .models import Order, OrderItem

class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['price']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_price', 'full_name', 'phone', 'created_at']
    list_filter = ['status', 'created_at', 'updated_at']
    search_fields = ['user__username', 'full_name', 'phone']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [OrderItemInline]
    actions = ['mark_as_paid', 'mark_as_shipped', 'export_orders_csv']

    def mark_as_paid(self, request, queryset):
        queryset.update(status=Order.Status.PAID)
        self.message_user(request, f'Статус изменен на "Оплачен" для {queryset.count()} заказов.')
    mark_as_paid.short_description = 'Отметить как оплаченные'

    def mark_as_shipped(self, request, queryset):
        queryset.update(status=Order.Status.SHIPPED)
        self.message_user(request, f'Статус изменен на "Отправлен" для {queryset.count()} заказов.')
    mark_as_shipped.short_description = 'Отметить как отправленные'

    def export_orders_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(['ID', 'Пользователь', 'Статус', 'Сумма', 'Дата'])
        for order in queryset:
            writer.writerow([order.id, order.user.username, order.get_status_display(), order.total_price, order.created_at])
        return response
    export_orders_csv.short_description = 'Экспортировать выбранные заказы в CSV'

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    list_filter = ['product__category']
    search_fields = ['order__user__username', 'product__name']


class OrderAnalytics(Order):
    class Meta:
        proxy = True
        verbose_name = 'Аналитика продаж'
        verbose_name_plural = 'Аналитика продаж'

@admin.register(OrderAnalytics)
class OrderAnalyticsAdmin(admin.ModelAdmin):
    change_list_template = 'admin/order_analytics_change_list.html'
    date_hierarchy = 'created_at'
    
    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context=extra_context)
        try:
            qs = response.context_data['cl'].queryset
        except (AttributeError, KeyError):
            return response
            
        metrics = {
            'total_revenue': qs.aggregate(Sum('total_price'))['total_price__sum'] or 0,
            'total_orders': qs.count(),
        }
        response.context_data['summary'] = metrics
        
        # Топ продукты (по количеству проданных)
        top_products = OrderItem.objects.filter(order__in=qs)\
            .values('product__name')\
            .annotate(total_sold=Sum('quantity'))\
            .order_by('-total_sold')[:5]
            
        response.context_data['top_products'] = top_products
        return response
