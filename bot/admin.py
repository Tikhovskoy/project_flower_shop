from django.contrib import admin
from django.utils.html import format_html
from FlowerShopBot import settings
from .models import Bouquet, Composition, Order, Consultation, OrderItem


class BouquetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'created_at', 'updated_at', 'preview')
    list_filter = ('is_available',)
    list_editable = ('is_available', 'price',)
    readonly_fields = ('created_at',)

    def preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}{}" style="width: 50px; height: 50px;"/>',
                settings.MEDIA_URL, obj.photo
            )
        return "Нет фото"

    preview.short_description = "Фото"


class CompositionAdmin(admin.ModelAdmin):
    list_display = ('name', 'event', 'price', 'is_available', 'updated_at', 'preview')
    list_filter = ('is_available',)
    list_editable = ('is_available', 'price',)
    readonly_fields = ('created_at',)

    def preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}{}" style="width: 50px; height: 50px;"/>',
                settings.MEDIA_URL, obj.photo
            )
        return "Нет фото"

    preview.short_description = "Фото"


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    fields = ('product', 'quantity')
    readonly_fields = ('product', 'quantity')


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'order_total', 'status', 'created_at', 'order_items_list')
    list_editable = ('status',)
    list_filter = ('status',)
    inlines = [OrderItemInline]

    @admin.display()
    def order_items_list(self, obj):
        items = obj.items.all()  # Получаем все OrderItem
        item_strings = []

        for item in items:
            product = item.product  # Используем product, а не content_object
            if product and hasattr(product, 'name'):
                item_strings.append(f"{product.name} (x{item.quantity})")
            else:
                item_strings.append(f"❌ Ошибка: товар {item.id} не найден")

        return ", ".join(item_strings) if item_strings else "Нет товаров"


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'budget', 'status', 'created_at', 'preferences')
    list_filter = ('status',)
    list_editable = ('status',)


admin.site.register(Bouquet, BouquetAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Consultation, ConsultationAdmin)
