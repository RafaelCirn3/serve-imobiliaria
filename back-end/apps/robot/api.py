import json

from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from apps.common.permissions import IsAdminUserOnly
from .extraction.document import MAX_BYTES, ExtractionError
from .extraction.service import commit_unit, inspect_table, review_unit, stage_table, validation_issues
from .models import TableImport, TableUnit


class TableUnitSerializer(serializers.ModelSerializer):
    validation_issues = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()

    def get_gallery(self, obj) -> dict | None:
        from .models import PropertyImageSelection

        if not obj.imported_property_id:
            return None
        return PropertyImageSelection.objects.filter(property_id=obj.imported_property_id).values_list("result", flat=True).first()

    def get_validation_issues(self, obj) -> dict:
        return validation_issues(obj)

    class Meta:
        model = TableUnit
        fields = ["id", "document", "index", "fields", "evidence", "warnings", "reviewed", "imported_property", "imported_at", "validation_issues", "gallery"]
        read_only_fields = fields


class TableImportSerializer(serializers.ModelSerializer):
    units = TableUnitSerializer(many=True, read_only=True)

    class Meta:
        model = TableImport
        fields = ["id", "filename", "source_folder_id", "drive_file_id", "content_sha256", "developer_profile", "parser_version", "context", "created_at", "units"]
        read_only_fields = fields


class UploadSerializer(serializers.Serializer):
    arquivo = serializers.FileField()
    contexto = serializers.CharField(required=False, default="{}", max_length=4096)
    source_folder_id = serializers.CharField(required=False, default="", max_length=128)
    drive_file_id = serializers.CharField(required=False, default="", max_length=128)
    preview = serializers.BooleanField(required=False, default=False)
    ocr = serializers.BooleanField(required=False, default=True)

    def validate_arquivo(self, value):
        if value.size > MAX_BYTES:
            raise serializers.ValidationError("Arquivo maior que 15 MB.")
        return value

    def validate_contexto(self, value):
        try:
            context = json.loads(value)
        except ValueError:
            raise serializers.ValidationError("Contexto deve ser um objeto JSON.")
        if not isinstance(context, dict):
            raise serializers.ValidationError("Contexto deve ser um objeto JSON.")
        return context


class ReviewSerializer(serializers.Serializer):
    fields = serializers.DictField(required=False, default=dict)
    approve = serializers.BooleanField(default=False)


class ImportOutcomeSerializer(serializers.Serializer):
    imovel_id = serializers.IntegerField()
    criado = serializers.BooleanField()
    status = serializers.CharField()
    dados_existentes_alterados = serializers.BooleanField()
    gallery = serializers.JSONField(allow_null=True)


class MGAImportViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUserOnly]
    serializer_class = TableImportSerializer
    queryset = TableImport.objects.prefetch_related("units").order_by("-created_at")
    parser_classes = [MultiPartParser, FormParser]

    @extend_schema(responses=OpenApiTypes.OBJECT)
    @action(detail=False, methods=["get"], url_path="sincronizacao")
    def synchronization_status(self, request):
        from django.conf import settings
        path=settings.BASE_DIR/"reports/mga/sync-result.json"
        if not path.exists():
            return Response({"status":"nao_executada"})
        try:
            report=json.loads(path.read_text(encoding="utf-8"))
        except (OSError,ValueError):
            return Response({"status":"atualizando"})
        status="concluida" if report.get("finished_at") else "em_execucao"
        if report.get("finished_at") and (report.get("errors") or report.get("source_errors")):
            status="parcial"
        return Response({"status":status,**report})

    @extend_schema(request=UploadSerializer, responses={200: OpenApiTypes.OBJECT, 201: TableImportSerializer})
    def create(self, request):
        serializer = UploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        file = values["arquivo"]
        try:
            result = inspect_table(file.read(MAX_BYTES + 1), file.name, context=values["contexto"], allow_ocr=values["ocr"])
        except ExtractionError as exc:
            raise serializers.ValidationError({"arquivo": str(exc)}) from None
        if values["preview"]:
            return Response({key: value for key, value in result.items() if key != "pages"})
        document, created = stage_table(result, source_folder_id=values["source_folder_id"], drive_file_id=values["drive_file_id"])
        return Response(TableImportSerializer(document).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)


class MGAUnitViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [IsAdminUserOnly]
    serializer_class = TableUnitSerializer
    queryset = TableUnit.objects.select_related("document", "imported_property")

    @extend_schema(request=ReviewSerializer, responses=TableUnitSerializer)
    def partial_update(self, request, pk=None):
        data = ReviewSerializer(data=request.data)
        data.is_valid(raise_exception=True)
        unit = review_unit(self.get_object().pk, data.validated_data["fields"], data.validated_data["approve"])
        return Response(TableUnitSerializer(unit).data)

    @extend_schema(request=None, responses={200: ImportOutcomeSerializer, 201: ImportOutcomeSerializer})
    @action(detail=True, methods=["post"], url_path="importar")
    def import_property(self, request, pk=None):
        property, created = commit_unit(self.get_object().pk)
        return Response({"imovel_id": property.pk, "criado": created, "status": property.status,
                         "dados_existentes_alterados": False, "gallery": TableUnitSerializer(self.get_object()).data["gallery"]}, status=201 if created else 200)
