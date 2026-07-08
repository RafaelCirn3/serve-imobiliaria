from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Region
from .serializers import RegionSerializer


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
