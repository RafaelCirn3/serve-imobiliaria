from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import AllowAny

from apps.common.permissions import IsAdminUserOnly

from .models import Banner, HomeContent, PropertyCarousel
from .serializers import BannerSerializer, HomeContentSerializer, AdminPropertyCarouselSerializer, PublicPropertyCarouselSerializer


class PublicBannerViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = BannerSerializer
    permission_classes = [AllowAny]
    queryset = Banner.objects.filter(ativo=True)
    ordering_fields = ["ordem"]

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        data = self.get_serializer(queryset, many=True).data
        return Response({"count": len(data), "next": None, "previous": None, "results": data})


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


class PublicPropertyCarouselViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = PublicPropertyCarouselSerializer
    queryset = PropertyCarousel.objects.filter(ativo=True).prefetch_related("imoveis")

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = self.get_serializer(queryset, many=True).data
        return Response({"count": len(data), "next": None, "previous": None, "results": data})


class AdminPropertyCarouselViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAdminUserOnly]
    serializer_class = AdminPropertyCarouselSerializer
    queryset = PropertyCarousel.objects.all()

    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        data = self.get_serializer(queryset, many=True).data
        return Response({"count": len(data), "next": None, "previous": None, "results": data})
