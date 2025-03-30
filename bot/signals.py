from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from bot.models import OrderItem


@receiver(post_save, sender=OrderItem)
@receiver(post_delete, sender=OrderItem)
def update_order_total(sender, instance, **kwargs):
    """Пересчитывает сумму заказа при изменении товаров в заказе"""
    order = instance.order
    order.calculate_total()

