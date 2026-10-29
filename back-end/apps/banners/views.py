from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Banner, HomeContent
from .serializers import BannerSerializer, HomeContentSerializer


class PublicBannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    queryset = Banner.objects.filter(ativo=True)
    ordering_fields = ["ordem"]


class AdminBannerViewSet(viewsets.ModelViewSet):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = BannerSerializer
    permission_classes = [IsAdminUserOnly]
    queryset = Banner.objects.all()
    ordering_fields = ["ordem"]


class HomeContentView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        config, _ = HomeContent.objects.get_or_create(pk=1)
        return Response(HomeContentSerializer(config).data)


class AdminHomeContentView(APIView):
    permission_classes = [IsAdminUserOnly]

    def patch(self, request):
        config, _ = HomeContent.objects.get_or_create(pk=1)
        serializer = HomeContentSerializer(config, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
