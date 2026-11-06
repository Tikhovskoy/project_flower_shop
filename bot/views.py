from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, viewsets
from rest_framework.filters import OrderingFilter
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response

from .filters import BouquetFilter, CompositionFilter
from .models import Bouquet, Composition, Consultation, Order
from .permissions import IsAdminOrReadOnly
from .serializers import (
    BouquetSerializer,
    CompositionSerializer,
    ConsultationSerializer,
    OrderItemSerializer,
    OrderSerializer,
)


class BouquetViewSet(viewsets.ModelViewSet):
    queryset = Bouquet.objects.all()
    serializer_class = BouquetSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = BouquetFilter


class CompositionViewSet(viewsets.ModelViewSet):
    queryset = Composition.objects.all()
    serializer_class = CompositionSerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_class = CompositionFilter


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]


class ConsultationViewSet(viewsets.ModelViewSet):
    queryset = Consultation.objects.all()
    serializer_class = ConsultationSerializer
    permission_classes = [IsAdminUser]


class OrderCreateView(generics.CreateAPIView):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    permission_classes = [IsAdminUser]

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        items_data = data.pop("items", [])
        order_serializer = OrderSerializer(data=data)

        if order_serializer.is_valid():
            order = order_serializer.save()
            for item in items_data:
                item_serializer = OrderItemSerializer(data=item)
                if item_serializer.is_valid():
                    item_serializer.save(order=order)
                else:
                    return Response(item_serializer.errors, status=400)
            return Response(OrderSerializer(order).data, status=201)
        return Response(order_serializer.errors, status=400)
