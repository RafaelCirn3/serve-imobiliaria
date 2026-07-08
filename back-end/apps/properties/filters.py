import django_filters

from .models import Property


class PropertyFilter(django_filters.FilterSet):
    valor_min = django_filters.NumberFilter(field_name="valor", lookup_expr="gte")
    valor_max = django_filters.NumberFilter(field_name="valor", lookup_expr="lte")
    area_min = django_filters.NumberFilter(field_name="area_privativa", lookup_expr="gte")
    area_max = django_filters.NumberFilter(field_name="area_privativa", lookup_expr="lte")
    quartos = django_filters.NumberFilter(field_name="quartos", lookup_expr="gte")
    suites = django_filters.NumberFilter(field_name="suites", lookup_expr="gte")
    vagas = django_filters.NumberFilter(field_name="vagas", lookup_expr="gte")

    class Meta:
        model = Property
        fields = [
            "cidade",
            "bairro",
            "tipo",
            "finalidade",
            "destaque",
            "status",
            "valor_min",
            "valor_max",
            "quartos",
            "suites",
            "vagas",
            "area_min",
            "area_max",
        ]
