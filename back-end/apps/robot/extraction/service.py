"""Serviço compartilhado por CLI, API e MCP; inserção apenas como rascunho."""

from dataclasses import asdict
import hashlib
import json
from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.properties.serializers import AdminPropertySerializer
from apps.robot.models import ImportedUnitIdentity, TableImport, TableUnit
from apps.robot.profiles import normalize
from .document import DocumentExtractor, ExtractionError
from .mga import MGATableParser


CONTEXT_FIELDS = {"empreendimento", "cidade", "bairro", "tipo", "finalidade", "construtora", "endereco", "natureza_area"}
EDITABLE_FIELDS = {"empreendimento", "unidade", "torre", "andar", "tipologia", "valor", "area_informada", "medidas", "cidade", "bairro", "uf", "endereco", "tipo", "finalidade", "descricao", "construtora", "quartos", "suites", "vagas", "mobiliado"}
EDITABLE_FIELDS |= {"previsao_entrega", "registro_incorporacao"}
EDITABLE_FIELDS |= {"area_total", "area_privativa", "logradouro", "numero", "complemento", "cep"}


def inspect_table(content, filename, context=None, allow_ocr=True, extractor=None):
    context = context or {}
    if set(context) - CONTEXT_FIELDS:
        raise ExtractionError("Contexto contém campos desconhecidos.")
    if any(not isinstance(value, str) or len(value) > 255 for value in context.values()):
        raise ExtractionError("Contexto deve conter textos de até 255 caracteres.")
    if context.get("natureza_area") not in (None, "total", "privativa"):
        raise ExtractionError("Natureza da área deve ser total ou privativa.")
    pages = (extractor or DocumentExtractor()).extract(content, filename, allow_ocr=allow_ocr)
    units = MGATableParser().parse(pages, context)
    return {"parser_version": MGATableParser.version, "content_sha256": hashlib.sha256(content).hexdigest(),
            "filename": filename, "context": context, "pages": [asdict(page) for page in pages],
            "units": [unit.as_dict() for unit in units], "warnings": [] if units else ["LAYOUT_NAO_RECONHECIDO_OU_SEM_UNIDADES"]}


@transaction.atomic
def stage_table(result, source_folder_id="", drive_file_id=""):
    identity = hashlib.sha256(json.dumps([result["content_sha256"], result["parser_version"], result["context"]], sort_keys=True).encode()).hexdigest()
    document, created = TableImport.objects.get_or_create(identity=identity, defaults={
        "content_sha256": result["content_sha256"], "filename": result["filename"][:255], "source_folder_id": source_folder_id,
        "drive_file_id": drive_file_id, "parser_version": result["parser_version"], "context": result["context"],
        "extraction": {"pages": [{key: page[key] for key in ("number", "method", "text", "width", "height")} for page in result["pages"]], "warnings": result["warnings"]},
    })
    if created:
        TableUnit.objects.bulk_create([TableUnit(document=document, index=index, fields=unit["fields"], warnings=unit["warnings"],
            evidence={key: value for key, value in unit.items() if key != "fields"}) for index, unit in enumerate(result["units"], start=1)])
    origin = {"filename": result["filename"], "source_folder_id": source_folder_id, "drive_file_id": drive_file_id}
    document = TableImport.objects.select_for_update().get(pk=document.pk)
    origins = document.extraction.get("origins", [])
    if origin not in origins:
        document.extraction = {**document.extraction, "origins": [*origins, origin]}
        document.save(update_fields=["extraction"])
    return document, created


def property_payload(unit):
    data = {key: value for key, value in unit.fields.items() if key in EDITABLE_FIELDS | {"origem_comercial"}}
    name, number = data.get("empreendimento", ""), data.get("unidade", "")
    data["titulo"] = f"{name} — unidade {number}"[:180]
    data["descricao"] = data.get("descricao") or f"{name}, unidade {number}. Dados extraídos da tabela comercial; cadastro em revisão."
    data["status"] = "rascunho"
    from apps.locations.addressing import AddressNormalizer
    data.update(AddressNormalizer.parse(data))
    return data


def validation_issues(unit):
    serializer = AdminPropertySerializer(data=property_payload(unit), context=draft_context(unit))
    serializer.is_valid()
    errors = dict(serializer.errors)
    for key in ("empreendimento", "unidade"):
        if not unit.fields.get(key):
            errors[key] = ["Campo obrigatório para identificar a unidade."]
    try:
        value = Decimal(str(unit.fields.get("valor")))
        valid_value = value.is_finite() and value > 0
    except InvalidOperation:
        valid_value = False
    if not valid_value:
        errors["valor"] = ["Preço total positivo e explícito obrigatório."]
    return errors


def draft_context(unit):
    return {"robot_draft": "avulsos" not in normalize(unit.document.filename, metadata=True)}


@transaction.atomic
def review_unit(unit_id, changes, approve=False):
    if set(changes) - EDITABLE_FIELDS:
        raise ValidationError("Campos de revisão não permitidos.")
    unit = TableUnit.objects.select_for_update().get(pk=unit_id)
    if unit.imported_property_id:
        schedule_location(unit.pk)
        raise ValidationError("Unidade já importada. Revise o imóvel pelo cadastro administrativo.")
    before = dict(unit.fields)
    unit.fields = {**unit.fields, **changes}
    if approve and validation_issues(unit):
        raise ValidationError(validation_issues(unit))
    unit.reviewed = approve
    unit.evidence = {**unit.evidence, "reviews": [*unit.evidence.get("reviews", []),
                     {"before": before, "changes": changes, "approved": approve, "at": timezone.now().isoformat()}]}
    unit.save(update_fields=["fields", "reviewed", "evidence"])
    return unit


@transaction.atomic
def commit_unit(unit_id, with_images=True):
    unit = TableUnit.objects.select_for_update().select_related("document").get(pk=unit_id)
    if unit.imported_property_id:
        if with_images:
            schedule_images(unit.pk)
        return unit.imported_property, False
    errors = validation_issues(unit)
    if errors:
        raise ValidationError(errors)
    if not unit.reviewed and any(warning in unit.warnings for warning in ("OCR_REQUER_CONFERENCIA", "UNIDADE_NAO_DISPONIVEL", "UNIDADE_DUPLICADA_NO_DOCUMENTO", "BAIXA_CONFIANCA_OCR", "CONFLITO_FINALIDADE", "CONFLITO_TIPOLOGIA", "PRECO_SUSPEITO")):
        raise ValidationError("Conferência explícita obrigatória para preço suspeito, OCR, conflitos, indisponibilidade ou unidade duplicada.")
    # Sem condomínio/cidade/tipo/torre/unidade completos não há identidade segura.
    fields = property_payload(unit)
    key = hashlib.sha256("|".join(normalize(fields.get(field, "")) for field in
                         ("empreendimento", "cidade", "tipo", "finalidade", "torre", "unidade")).encode()).hexdigest()
    previous = ImportedUnitIdentity.objects.filter(key=key).first()
    if previous:
        # Versões posteriores ficam para revisão; nunca sobrescrever preço ou
        # disponibilidade de um imóvel já existente por uma tabela mais antiga.
        unit.imported_property = previous.property
        unit.imported_at = timezone.now()
        unit.evidence = {**unit.evidence, "import_decision": {"created": False, "existing_price": str(previous.property.valor),
                         "table_price": str(fields["valor"]), "existing_data_changed": False}}
        unit.save(update_fields=["imported_property", "imported_at", "evidence"])
        schedule_location(unit.pk)
        if with_images:
            schedule_images(unit.pk)
        return previous.property, False
    serializer = AdminPropertySerializer(data=property_payload(unit), context=draft_context(unit))
    serializer.is_valid(raise_exception=True)
    created = True
    try:
        with transaction.atomic():
            avulso = "avulsos" in normalize(unit.document.filename, metadata=True)
            property = serializer.save(status="rascunho", agrupar_publicacao=not avulso)
            ImportedUnitIdentity.objects.create(key=key, property=property)
    except IntegrityError:
        previous = ImportedUnitIdentity.objects.filter(key=key).first()
        if previous is None:
            raise ValidationError("Conflito de importação concorrente; repita a operação.") from None
        property, created = previous.property, False
    unit.imported_property = property
    unit.imported_at = timezone.now()
    unit.save(update_fields=["imported_property", "imported_at"])
    schedule_location(unit.pk)
    if with_images:
        schedule_images(unit.pk)
    return property, created


def schedule_images(unit_id):
    from apps.robot.gallery import attach_after_commit

    transaction.on_commit(lambda: attach_after_commit(unit_id))


def schedule_location(unit_id):
    transaction.on_commit(lambda: resolve_location(unit_id))


def resolve_location(unit_id):
    from apps.locations.resolution import AddressResolver

    unit = TableUnit.objects.select_related("imported_property").get(pk=unit_id)
    if not unit.imported_property_id:
        return
    try:
        result = AddressResolver().apply(unit.imported_property)
    except Exception as exc:
        result = {"warnings": ["LOCALIZACAO_PENDENTE"], "error": type(exc).__name__}
    with transaction.atomic():
        unit = TableUnit.objects.select_for_update().get(pk=unit_id)
        unit.evidence = {**unit.evidence, "location_resolution": result}
        unit.save(update_fields=["evidence"])
