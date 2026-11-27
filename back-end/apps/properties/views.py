from django.db.models import Q, Max, Count, OuterRef, Subquery, Case, When, F, DecimalField
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
from .serializers import MapPropertySerializer, PublicUnitSerializer
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

    def filter_queryset(self, queryset):
        # Filter units first, so a matching unit never disappears just because
        # another unit represents its tower. Then emit only one card per group.
        queryset = super().filter_queryset(queryset)
        representative = queryset.filter(grupo_publicacao=OuterRef("grupo_publicacao")).order_by("id").values("pk")[:1]
        queryset = queryset.filter(Q(grupo_publicacao="") | Q(pk=Subquery(representative)))
        ordering = queryset.query.order_by
        if any(field.lstrip("-") == "valor" for field in ordering):
            minimum = Property.objects.filter(status=Property.Status.PUBLICADO,
                grupo_publicacao=OuterRef("grupo_publicacao")).order_by("valor").values("valor")[:1]
            queryset = queryset.annotate(publication_price=Case(
                When(grupo_publicacao="", then=F("valor")), default=Subquery(minimum),
                output_field=DecimalField(max_digits=14, decimal_places=2)))
            queryset = queryset.order_by(*(field.replace("valor", "publication_price") if field.lstrip("-") == "valor" else field for field in ordering), "pk")
        return queryset

    def retrieve(self, request, *args, **kwargs):
        property = self.public_property(kwargs["slug"])
        if property.grupo_publicacao:
            property = self.get_queryset().filter(grupo_publicacao=property.grupo_publicacao).order_by("id").first()
        return Response(self.get_serializer(property).data)

    def public_property(self, slug):
        from django.shortcuts import get_object_or_404
        import re

        suffix = slug.rsplit("-", 1)[-1]
        if re.fullmatch(r"[a-f0-9]{64}", suffix):
            return get_object_or_404(self.get_queryset().filter(grupo_publicacao=suffix).order_by("id")[:1])
        return get_object_or_404(self.get_queryset(), slug=slug)

    @action(detail=True, methods=["get"], url_path="unidades")
    def units(self, request, slug=None):
        from django.shortcuts import get_object_or_404

        property = self.public_property(slug)
        queryset = self.get_queryset().filter(grupo_publicacao=property.grupo_publicacao) if property.grupo_publicacao else self.get_queryset().filter(pk=property.pk)
        # Exact prices remain available independently of the rounded headline.
        rows = PublicUnitSerializer(queryset.order_by("valor"), many=True).data
        seen, options = set(), []
        for row in rows:
            signature = tuple(row.items())
            if signature not in seen:
                seen.add(signature)
                options.append(row)
        return Response(options)

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
        queryset = self.filter_queryset(self.get_queryset().filter(destaque=True).order_by("-valor"))
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

    @action(detail=False, methods=["get"], url_path="resumo")
    def summary(self, request):
        from apps.leads.models import Lead
        counts = self.get_queryset().aggregate(
            total=Count('id', distinct=True),
            publicados=Count('id', filter=Q(status='publicado'), distinct=True),
            rascunhos=Count('id', filter=Q(status='rascunho'), distinct=True),
            sem_fotos=Count('id', filter=Q(imagens__isnull=True), distinct=True),
        )
        return Response({**counts, 'leads': Lead.objects.count()})

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
