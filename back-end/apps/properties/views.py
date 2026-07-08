from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from apps.common.permissions import IsAdminUserOnly

from .filters import PropertyFilter
from .models import Property, PropertyImage
from .serializers import AdminPropertySerializer, PropertyImageSerializer, PublicPropertySerializer


class PublicPropertyViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = PublicPropertySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    filterset_class = PropertyFilter
    search_fields = ["titulo", "descricao", "bairro", "cidade"]
    ordering_fields = ["valor", "publicado_em", "destaque"]

    def get_queryset(self):
        return Property.objects.prefetch_related("imagens").filter(status=Property.Status.PUBLICADO)

    @action(detail=False, methods=["get"], url_path="destaques")
    def destaques(self, request):
        queryset = self.filter_queryset(self.get_queryset().filter(destaque=True))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        return Response(self.get_serializer(queryset, many=True).data)

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

        created = []
        capa_requested = str(request.data.get("imagem_capa", "")).lower() in {"1", "true", "sim"}
        for index, file in enumerate(files):
            image = PropertyImage.objects.create(
                imovel=imovel,
                imagem=file,
                legenda=request.data.get("legenda", ""),
                ordem=request.data.get("ordem", index),
                imagem_capa=capa_requested and index == 0,
            )
            created.append(image)

        return Response(PropertyImageSerializer(created, many=True, context={"request": request}).data, status=status.HTTP_201_CREATED)

    @action(
        detail=True,
        methods=["patch", "delete"],
        url_path=r"imagens/(?P<image_pk>[^/.]+)",
        parser_classes=[MultiPartParser, FormParser],
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
