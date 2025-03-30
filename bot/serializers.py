from rest_framework import serializers
from .models import Bouquet, Composition, Order, OrderItem, Consultation


class BouquetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bouquet
        fields = '__all__'


class CompositionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Composition
        fields = '__all__'


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ['content_type', 'object_id', 'quantity']


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)  # `required=True` не нужен, потому что `many=True`

    class Meta:
        model = Order
        fields = ['id', 'customer_name', 'phone_number', 'delivery_address', 'items', 'postcard']

    def create(self, validated_data):
        items_data = validated_data.pop('items', [])  # Получаем список товаров
        order = Order.objects.create(**validated_data)  # Создаём заказ

        # Создаём OrderItem для каждого товара
        for item_data in items_data:
            OrderItem.objects.create(order=order, **item_data)

        return order



class ConsultationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Consultation
        fields = '__all__'
