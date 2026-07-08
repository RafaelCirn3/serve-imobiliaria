from rest_framework import viewsets
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Banner
from .serializers import BannerSerializer


class PublicBannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    queryset = Banner.objects.filter(ativo=True)
    ordering_fields = ["ordem"]


class AdminBannerViewSet(viewsets.ModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [IsAdminUserOnly]
    queryset = Banner.objects.all()
    ordering_fields = ["ordem"]
