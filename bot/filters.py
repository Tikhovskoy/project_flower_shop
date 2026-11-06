from django_filters import rest_framework as filters

from .models import Bouquet, Composition


class CatalogFilter(filters.FilterSet):
    """Общие фильтры каталога: диапазон цен и наличие.

    Цена ищется в поле `price_field`: у букета это его собственная цена, у композиции —
    цена входящих в неё букетов.
    """

    price_field = "price"

    is_available = filters.BooleanFilter()
    min_price = filters.NumberFilter(method="filter_min_price")
    max_price = filters.NumberFilter(method="filter_max_price")

    def filter_min_price(self, queryset, name, value):
        return self._by_price(queryset, "gte", value)

    def filter_max_price(self, queryset, name, value):
        return self._by_price(queryset, "lte", value)

    def _by_price(self, queryset, lookup, value):
        queryset = queryset.filter(**{f"{self.price_field}__{lookup}": value})
        # Через связь «многие ко многим» одна композиция может подойти несколько раз
        return queryset.distinct() if "__" in self.price_field else queryset


class BouquetFilter(CatalogFilter):
    class Meta:
        model = Bouquet
        fields = ["price"]


class CompositionFilter(CatalogFilter):
    price_field = "bouquets__price"

    class Meta:
        model = Composition
        fields = ["event"]
