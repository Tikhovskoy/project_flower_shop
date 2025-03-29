from django.contrib import admin
from django.utils.html import format_html
from django.utils.timezone import localtime
import pytz

from FlowerShopBot import settings
from .models import Bouquet, Composition, Order, Consultation


class BouquetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'created_at', 'updated_at', 'preview')
    list_filter = ('is_available',)
    list_editable = ('is_available', 'price',)

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
    filter_vertical = ('bouquets',)

    def preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}{}" style="width: 50px; height: 50px;"/>',
                settings.MEDIA_URL, obj.photo
            )
        return "Нет фото"

    preview.short_description = "Фото"

class OrderAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'bouquet', 'phone', 'formatted_delivery_time', 'short_card_text', 'status', 'formatted_created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('customer_name', 'phone', 'bouquet__name', 'card_text')
    readonly_fields = ('created_at',)
    list_editable = ('status',)

    def formatted_delivery_time(self, obj):
        if obj.delivery_time:
            local_time = localtime(obj.delivery_time, pytz.timezone('Asia/Krasnoyarsk'))
            return local_time.strftime('%d.%m.%Y %H:%M')
        return "-"
    formatted_delivery_time.short_description = "Время доставки"

    def formatted_created_at(self, obj):
        if obj.created_at:
            local_time = localtime(obj.created_at, pytz.timezone('Asia/Krasnoyarsk'))
            return local_time.strftime('%d.%m.%Y %H:%M')
        return "-"
    formatted_created_at.short_description = "Время заказа"

    def short_card_text(self, obj):
        if obj.card_text:
            return (obj.card_text[:50] + '...') if len(obj.card_text) > 50 else obj.card_text
        return "-"
    short_card_text.short_description = "Открытка"

class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('user_id', 'phone', 'status', 'formatted_created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('phone',)

    def formatted_created_at(self, obj):
        if obj.created_at:
            local_time = localtime(obj.created_at, pytz.timezone('Asia/Krasnoyarsk'))
            return local_time.strftime('%d.%m.%Y %H:%M')
        return "-"
    formatted_created_at.short_description = "Время запроса"


admin.site.register(Bouquet, BouquetAdmin)
admin.site.register(Composition, CompositionAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(Consultation, ConsultationAdmin)
