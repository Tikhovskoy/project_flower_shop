from django.contrib import admin
from django.utils.html import format_html
from FlowerShopBot import settings
from .models import Bouquet, Composition, Order, Consultation


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


class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'customer_name', 'order_total', 'status', 'created_at')
    list_editable = ('status',)
    list_filter = ('status',)


class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'budget', 'status', 'created_at')
    list_filter = ('status',)
    list_editable = ('status',)


admin.site.register(Bouquet, BouquetAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Consultation, ConsultationAdmin)
