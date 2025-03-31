from django.contrib import admin
from django.utils.html import format_html
from FlowerShopBot import settings
from .models import Bouquet, Composition, Order, Consultation, OrderItem


class BouquetAdmin(admin.ModelAdmin):
    list_display = (
        'name', 'price', 'is_available', 'short_poetic_text',
        'created_at', 'updated_at', 'preview'
    )
    list_filter = ('is_available',)
    list_editable = ('is_available', 'price',)
    readonly_fields = ('created_at', 'updated_at', 'preview')
    search_fields = ('name', 'description')

    def preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}{}" style="width: 50px; height: 50px; object-fit: cover;"/>',
                settings.MEDIA_URL, obj.photo
            )
        return "Нет фото"
    preview.short_description = "Фото"

    def short_poetic_text(self, obj):
        if obj.poetic_text:
            return (obj.poetic_text[:50] + '...') if len(obj.poetic_text) > 50 else obj.poetic_text
        return "-"
    short_poetic_text.short_description = "Поэтичный текст"


class CompositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'event')
    filter_vertical = ('bouquets',)
    search_fields = ('name',)


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ('product', 'quantity')
    fields = ('product', 'quantity')
    can_delete = False
    show_change_link = False


class OrderAdmin(admin.ModelAdmin):
    list_display = (
        'id', 'customer_name', 'phone_number', 'order_total', 'status',
        'payment_method', 'created_at', 'order_items_list', 'delivery_time', 'postcard',
    )
    list_editable = ('status',)
    list_filter = ('status', 'payment_method')
    inlines = [OrderItemInline]
    readonly_fields = ('created_at', 'order_total', 'delivery_time')
    search_fields = ('customer_name', 'phone_number')

    @admin.display(description="Состав заказа")
    def order_items_list(self, obj):
        items = obj.items.all()
        item_strings = []
        for item in items:
            product = item.product
            if product and hasattr(product, 'name'):
                item_strings.append(f"{product.name} (x{item.quantity})")
            else:
                item_strings.append(f"❌ Товар не найден")
        return ", ".join(item_strings) if item_strings else "–"


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'budget', 'status', 'created_at', 'preferences')
    list_filter = ('status',)
    list_editable = ('status',)
    readonly_fields = ('created_at',)
    search_fields = ('name', 'phone_number', 'preferences')


admin.site.register(Bouquet, BouquetAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Consultation, ConsultationAdmin)
