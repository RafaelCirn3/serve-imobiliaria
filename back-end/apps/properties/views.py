from django.db.models import Q, Max
from rest_framework import status, viewsets, serializers
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser, JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.permissions import IsAdminUserOnly

from .filters import PropertyFilter
from apps.common.images import prepare_images
from django.db import transaction

from .models import Property, PropertyImage
from .serializers import AdminPropertySerializer, PropertyImageSerializer, PublicPropertySerializer
from .serializers import MapPropertySerializer
from django.conf import settings


class PublicPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicPropertySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_class = PropertyFilter
    search_fields = ["titulo", "descricao", "bairro", "cidade", "logradouro"]
    ordering_fields = ["valor", "publicado_em", "destaque"]

    def get_queryset(self):
        return Property.objects.prefetch_related("imagens").filter(status=Property.Status.PUBLICADO)

    @action(detail=False, methods=["get"], url_path="mapa")
    def map_properties(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        total = queryset.count()
        located = queryset.filter(latitude__isnull=False, longitude__isnull=False)
        located_count = located.count()
        limit = settings.MAP_RESULT_LIMIT
        data = MapPropertySerializer(located[:limit], many=True, context={"request": request}).data
        return Response({"count": total, "geolocalizados": located_count,
                         "sem_coordenadas": total - located_count, "limite": limit,
                         "truncado": located_count > limit, "results": data})

    @action(detail=False, methods=["get"], url_path="destaques")
    def destaques(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(destaque=True))
        return Response({"count": queryset.count(), "next": None, "previous": None,
                         "results": self.get_serializer(queryset, many=True).data})

    @action(detail=False, methods=["get"], url_path="busca")
    def busca(self, request):
        termo = request.query_params.get("q", "")
        queryset = self.filter_queryset(self.get_queryset())
        if termo:
            queryset = queryset.filter(
                Q(titulo__icontains=termo)
                | Q(descricao__icontains=termo)
                | Q(bairro__icontains=termo)
                | Q(cidade__icontains=termo)
                | Q(logradouro__icontains=termo)
            )
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)


class AdminPropertyViewSet(viewsets.ModelViewSet):
    serializer_class = AdminPropertySerializer
    permission_classes = [IsAdminUserOnly]
    queryset = Property.objects.prefetch_related("imagens").all()
    filterset_class = PropertyFilter
    search_fields = ["titulo", "descricao", "bairro", "cidade"]
    ordering_fields = ["valor", "publicado_em", "destaque", "criado_em"]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.status = Property.Status.INATIVO
        instance.save(update_fields=["status", "atualizado_em"])
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=["post"],
        url_path="imagens",
        parser_classes=[MultiPartParser, FormParser],
    )
    def upload_images(self, request, pk=None):
        imovel = self.get_object()
        files = request.FILES.getlist("imagens") or request.FILES.getlist("imagem")
        if not files:
            return Response({"detail": "Envie um ou mais arquivos no campo imagens."}, status=status.HTTP_400_BAD_REQUEST)

        files = prepare_images(files)
        created = []
        capa_requested = str(request.data.get("imagem_capa", "")).lower() in {"1", "true", "sim"}
        metadata = serializers.Serializer(data=request.data)
        metadata.fields['legenda'] = serializers.CharField(max_length=180, required=False, allow_blank=True, default='')
        metadata.fields['ordem'] = serializers.IntegerField(min_value=0, required=False)
        metadata.is_valid(raise_exception=True)
        start = metadata.validated_data.get('ordem', (imovel.imagens.aggregate(last=Max('ordem'))['last'] or 0) + 1)
        stored = []
        try:
            with transaction.atomic():
                for index, file in enumerate(files):
                    image = PropertyImage(imovel=imovel, legenda=metadata.validated_data['legenda'],
                                          ordem=start + index, imagem_capa=capa_requested and index == 0)
                    image.imagem.save(file.name, file, save=False)
                    stored.append(image.imagem)
                    image.save()
                    created.append(image)
        except Exception:
            for image in stored:
                image.delete(save=False)
            raise

        return Response(PropertyImageSerializer(created, many=True, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"imagens/(?P<image_pk>[^/.]+)",
        parser_classes=[MultiPartParser, FormParser, JSONParser],
    )
    def image_detail(self, request, pk=None, image_pk=None):
        imovel = self.get_object()
        image = PropertyImage.objects.filter(imovel=imovel, pk=image_pk).first()
        if image is None:
            return Response({"detail": "Imagem não encontrada."}, status=status.HTTP_404_NOT_FOUND)

        if request.method == "DELETE":
            image.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        serializer = PropertyImageSerializer(image, data=request.data, partial=True, context={"request": request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
