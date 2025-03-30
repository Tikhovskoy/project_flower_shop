from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class Bouquet(models.Model):
    name = models.CharField('Название букета:', max_length=100)
    description = models.TextField('Описание и состав букета:', blank=True)
    price = models.IntegerField('Цена в Р:')
    photo = models.ImageField('Фото букета:', upload_to='bouquets/', blank=True, null=True)
    is_available = models.BooleanField('В продаже:', default=True)
    created_at = models.DateTimeField('Дата добавления букета:', auto_now_add=True)
    updated_at = models.DateTimeField('Дата последнего изменения:', auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.price}₽)"


class Composition(models.Model):
    EVENT_CHOICES = [
        ('wedding', 'Для свадьбы'),
        ('march8', '8 марта'),
        ('teacher', 'Для учителя'),
        ('no_reason', 'Без повода'),
    ]

    name = models.CharField('Название композиции:', max_length=100)
    description = models.TextField('Описание и состав композиции:', blank=True)
    price = models.IntegerField('Цена в Р:')
    photo = models.ImageField('Фото композиции:', upload_to='compositions/', blank=True, null=True)
    is_available = models.BooleanField('В продаже:', default=True)
    created_at = models.DateTimeField('Дата добавления композиции:', auto_now_add=True)
    updated_at = models.DateTimeField('Дата последнего изменения:', auto_now=True)
    event = models.CharField('Мероприятие:', max_length=20, choices=EVENT_CHOICES, default='no_reason')

    def __str__(self):
        return f"{self.name} ({self.price}₽) — {self.get_event_display()}"


class Order(models.Model):
    PAYMENT_CHOICES = [
        ('cash', 'Наличные'),
        ('card', 'Банковская карта'),
        ('online', 'Онлайн-оплата'),
    ]

    STATUS_CHOICES = [
        ('accepted', 'Принят'),
        ('processing', 'В работе'),
        ('on_delivery', 'На доставке'),
        ('completed', 'Завершён'),
    ]

    customer_name = models.CharField('Имя покупателя:', max_length=200)
    created_at = models.DateTimeField('Время поступления заказа:', auto_now_add=True)
    phone_number = models.CharField('Телефон:', max_length=20)
    delivery_address = models.TextField('Адрес доставки:')
    order_total = models.DecimalField('Сумма заказа:', max_digits=10, decimal_places=2, default=0)
    postcard = models.TextField('Текст открытки:', default='')
    payment_method = models.CharField('Способ оплаты:', max_length=10, choices=PAYMENT_CHOICES, default='cash')
    status = models.CharField('Статус заказа:', max_length=15, choices=STATUS_CHOICES, default='accepted')

    def calculate_total(self):
        total = sum(item.product.price * item.quantity for item in self.items.all())
        self.order_total = total
        self.save()

    def __str__(self):
        return f"Заказ #{self.id} - {self.customer_name} ({self.get_status_display()})"

    def get_items(self):
        return self.items.all()


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    product = GenericForeignKey('content_type', 'object_id')
    quantity = models.PositiveIntegerField(default=1, verbose_name='Количество')

    def __str__(self):
        return f"{self.product} (x{self.quantity})"


class Consultation(models.Model):
    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершена'),
    ]

    name = models.CharField('Имя покупателя:', max_length=100)
    phone_number = models.CharField('Телефон:', max_length=20)
    budget = models.IntegerField('Ориентировочный бюджет:', blank=True, null=True)
    preferences = models.TextField('Пожелания клиента:', blank=True)
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')
    created_at = models.DateTimeField('Дата заявки:', auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.phone_number}) – {self.created_at.strftime('%d.%m.%Y %H:%M')}"
