import django_filters
from django import forms

from .models import Property
from apps.locations.normalization import normalized


class PropertyFilterForm(forms.Form):
    def clean(self):
        cleaned_data = super().clean()
        for minimum, maximum in (
            ("valor_min", "valor_max"),
            ("area_min", "area_max"),
            ("area_total_min", "area_total_max"),
        ):
            lower = cleaned_data.get(minimum)
            upper = cleaned_data.get(maximum)
            if lower is not None and upper is not None and lower > upper:
                self.add_error(maximum, "O máximo deve ser maior ou igual ao mínimo.")
        return cleaned_data


class PropertyFilter(django_filters.FilterSet):
    cidade = django_filters.CharFilter(method="filter_location")
    bairro = django_filters.CharFilter(method="filter_location")
    logradouro = django_filters.CharFilter(method="filter_location")
    cep = django_filters.CharFilter(method="filter_cep")

    def filter_location(self, queryset, name, value):
        return queryset.filter(**{f"{name}_busca": normalized(value)})

    def filter_cep(self, queryset, name, value):
        cep = value.replace("-", "").strip()
        if len(cep) != 8 or not cep.isascii() or not cep.isdigit():
            from rest_framework.exceptions import ValidationError
            raise ValidationError({"cep": "Informe um CEP com oito dígitos."})
        return queryset.filter(cep=cep)
    valor_min = django_filters.NumberFilter(field_name="valor", lookup_expr="gte", min_value=0)
    valor_max = django_filters.NumberFilter(field_name="valor", lookup_expr="lte", min_value=0)
    area_min = django_filters.NumberFilter(field_name="area_privativa", lookup_expr="gte", min_value=0)
    area_max = django_filters.NumberFilter(field_name="area_privativa", lookup_expr="lte", min_value=0)
    area_total_min = django_filters.NumberFilter(field_name="area_total", lookup_expr="gte", min_value=0)
    area_total_max = django_filters.NumberFilter(field_name="area_total", lookup_expr="lte", min_value=0)
    quartos = django_filters.NumberFilter(field_name="quartos", lookup_expr="gte", min_value=0)
    suites = django_filters.NumberFilter(field_name="suites", lookup_expr="gte", min_value=0)
    vagas = django_filters.NumberFilter(field_name="vagas", lookup_expr="gte", min_value=0)

    class Meta:
        model = Property
        form = PropertyFilterForm
        fields = [
            "cidade",
            "bairro",
            "logradouro",
            "cep",
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
            "area_total_min",
            "area_total_max",
        ]
