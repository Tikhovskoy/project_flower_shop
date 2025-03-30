from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from rest_framework import viewsets, generics
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.permissions import AllowAny
from .permissions import IsAdminOrReadOnly
from .models import Bouquet, Composition, Order, Consultation
from .serializers import BouquetSerializer, CompositionSerializer, OrderSerializer, ConsultationSerializer, \
    OrderItemSerializer


class BouquetViewSet(viewsets.ModelViewSet):
    queryset = Bouquet.objects.all()
    serializer_class = BouquetSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['is_available', 'price']
    filter_backends = [DjangoFilterBackend]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_available = self.request.query_params.get('is_available')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')

        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() in ['true', '1'])  # Явная фильтрация

        if min_price is not None:
            try:
                min_price = float(min_price)
                queryset = queryset.filter(price__gte=min_price)  # Цена больше или равна min_price
            except ValueError:
                pass

        if max_price is not None:
            try:
                max_price = float(max_price)
                queryset = queryset.filter(price__lte=max_price)  # Цена меньше или равна max_price
            except ValueError:
                pass

        return queryset


class CompositionViewSet(viewsets.ModelViewSet):
    queryset = Composition.objects.all()
    serializer_class = CompositionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filterset_fields = ['is_available', 'price', 'event']
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]

    def get_queryset(self):
        queryset = super().get_queryset()
        is_available = self.request.query_params.get('is_available')
        min_price = self.request.query_params.get('min_price')
        max_price = self.request.query_params.get('max_price')
        event = self.request.query_params.get('event')  # Исправлено

        if is_available is not None:
            queryset = queryset.filter(is_available=is_available.lower() == 'true')

        if event:
            queryset = queryset.filter(event=event)  # Исправлено

        try:
            if min_price is not None:
                queryset = queryset.filter(price__gte=float(min_price))
        except ValueError:
            print(f"⚠ Ошибка: Неверное значение min_price: {min_price}")

        try:
            if max_price is not None:
                queryset = queryset.filter(price__lte=float(max_price))
        except ValueError:
            print(f"⚠ Ошибка: Неверное значение max_price: {max_price}")

        return queryset


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminOrReadOnly]


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [AllowAny]


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        items_data = data.pop('items', [])  # Получаем список товаров
        order_serializer = OrderSerializer(data=data)

        if order_serializer.is_valid():
            order = order_serializer.save()
            for item in items_data:
                item["order"] = order  # ✅ Передаём объект, а не ID!
                item_serializer = OrderItemSerializer(data=item)
                if item_serializer.is_valid():
                    item_serializer.save(order=order)
                else:
                    return Response(item_serializer.errors, status=400)  # Ошибка в items
            return Response(OrderSerializer(order).data, status=201)  # ✅ Обновляем ответ
        return Response(order_serializer.errors, status=400)
