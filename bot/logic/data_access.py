from bot.models import Bouquet, Composition, Order, Consultation
from django.utils.timezone import make_aware
from datetime import datetime
import pytz

def get_bouquets(min_price=0, max_price=9999999):
    """
    Возвращаем букеты, подходящие по цене [min_price, max_price].
    """
    return list(Bouquet.objects.filter(
        is_available=True,
        price__gte=min_price,
        price__lte=max_price
    ))
    
def get_compositions(event=None, min_price=0, max_price=9999999):
    predefined_events = {"wedding", "march8", "teacher", "no_reason"}
    if not event or event not in predefined_events:
        return list(Bouquet.objects.filter(is_available=True, price__gte=min_price, price__lte=max_price))
    
    matching_bouquets = set()
    comps = Composition.objects.filter(event__contains=event, is_available=True)
    for c in comps:
        for b in c.bouquets.filter(is_available=True, price__gte=min_price, price__lte=max_price):
            matching_bouquets.add(b)
    return list(matching_bouquets)

def save_order(order_data: dict):
    """
    Сохранение заказа через Django ORM..
    """
    print(f"Сохранение заказа через data_access: {order_data}")

    delivery_time = order_data.get("delivery_time")
    if delivery_time and isinstance(delivery_time, str):
        delivery_time = datetime.fromisoformat(delivery_time)
    
    if delivery_time and delivery_time.tzinfo is None:
        delivery_time = make_aware(delivery_time, pytz.timezone('Asia/Krasnoyarsk'))
        
    Order.objects.create(
        bouquet_id=order_data["bouquet_id"],
        customer_name=order_data.get("customer_name", ""),
        address=order_data.get("address", ""),
        phone=order_data.get("phone", ""),
        delivery_time=delivery_time, 
        card_text=order_data.get("card_text", ""),
        status=order_data.get("status", "new"),
    )

def save_consultation(consultation_data: dict):
    """
    Сохранение консультации через Django ORM.
    """
    print(f"Сохранение консультации через data_access: {consultation_data}")
    Consultation.objects.create(
        user_id=consultation_data.get("user_id", 0),
        phone=consultation_data["phone"],
        status=consultation_data.get("status", "new")
    )
