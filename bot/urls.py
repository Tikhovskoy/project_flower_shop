from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import BouquetViewSet, CompositionViewSet, OrderViewSet, ConsultationViewSet, OrderCreateView


router = DefaultRouter()
router.register(r'bouquets', BouquetViewSet)
router.register(r'compositions', CompositionViewSet)
router.register(r'orders', OrderViewSet)
router.register(r'consultations', ConsultationViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('order/create/', OrderCreateView.as_view(), name='order-create'),
]

