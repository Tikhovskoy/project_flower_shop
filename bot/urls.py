from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    BouquetViewSet,
    CompositionViewSet,
    ConsultationViewSet,
    OrderCreateView,
    OrderViewSet,
)

router = DefaultRouter()
router.register(r"bouquets", BouquetViewSet)
router.register(r"compositions", CompositionViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"consultations", ConsultationViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("order/create/", OrderCreateView.as_view(), name="order-create"),
]
