from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Region
from .serializers import RegionSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from .services import lookup_cep, search_address
from .services import geocode_address
from .normalization import canonical_city, normalized
from apps.properties.models import Property
from rest_framework.exceptions import ValidationError
from django.conf import settings


class AddressThrottle(AnonRateThrottle):
    scope = "addresses"
    rate = "60/hour"

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}


class LocationViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]
    throttle_classes = [AddressThrottle]

    @action(detail=False, methods=["get"], url_path="mapa-config")
    def map_config(self, request):
        return Response({"tile_url": settings.MAP_TILE_URL, "attribution": settings.MAP_TILE_ATTRIBUTION})

    @action(detail=False, methods=["get"], url_path="cep")
    def cep(self, request):
        return Response(lookup_cep(request.query_params.get("cep", "")))

    @action(detail=False, methods=["get"], url_path="enderecos")
    def addresses(self, request):
        return Response(search_address(request.query_params.get("cidade", ""), request.query_params.get("logradouro", "")))

    @action(detail=False, methods=["post"], url_path="geocodificar", permission_classes=[IsAdminUserOnly])
    def geocode(self, request):
        return Response(geocode_address(request.data))

    def published_in_city(self, request):
        city = canonical_city(request.query_params.get("cidade", ""))
        if not city:
            raise ValidationError({"cidade": "Selecione uma cidade atendida."})
        return Property.objects.filter(status="publicado", cidade_busca=normalized(city))

    @action(detail=False, methods=["get"], url_path="bairros")
    def neighborhoods(self, request):
        return Response(self.options(self.published_in_city(request), "bairro"))

    @action(detail=False, methods=["get"], url_path="ruas")
    def streets(self, request):
        neighborhood = request.query_params.get("bairro", "")
        if not normalized(neighborhood):
            raise ValidationError({"bairro": "Selecione um bairro."})
        queryset = self.published_in_city(request).filter(bairro_busca=normalized(neighborhood))
        return Response(self.options(queryset, "logradouro"))

    @staticmethod
    def options(queryset, field):
        names = {}
        for value in queryset.exclude(**{field: ""}).order_by(field).values_list(field, flat=True).distinct():
            names.setdefault(normalized(value), " ".join(value.split()))
        return sorted(names.values(), key=normalized)


class PublicRegionViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [AllowAny]
    queryset = Region.objects.filter(ativo=True)
    filterset_fields = ["cidade", "ativo"]
    search_fields = ["nome", "cidade", "descricao"]
    ordering_fields = ["nome", "cidade"]


class AdminRegionViewSet(viewsets.ModelViewSet):
    serializer_class = RegionSerializer
    permission_classes = [IsAdminUserOnly]
    queryset = Region.objects.all()
    filterset_fields = ["cidade", "ativo"]
    search_fields = ["nome", "cidade", "descricao"]
    ordering_fields = ["nome", "cidade"]
