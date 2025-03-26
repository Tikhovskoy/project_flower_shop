from django.contrib import admin
from django.utils.html import format_html

from FlowerShopBot import settings
from .models import Bouquet


class BouquetAdmin(admin.ModelAdmin):
    list_display = ('name', 'price', 'is_available', 'created_at', 'updated_at', 'preview')
    list_filter = ('is_available',)
    list_editable = ('is_available',)

    def preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}{}" style="width: 50px; height: 50px;"/>',
                settings.MEDIA_URL, obj.photo
            )
        return "Нет фото"

    preview.short_description = "Фото"


admin.site.register(Bouquet, BouquetAdmin)
