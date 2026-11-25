"""Publication standard approved by the operator for MGA imports."""

from collections import Counter

from django.db import transaction
from django.utils import timezone

from apps.properties.models import Property
from apps.properties.publications import PublicationPolicy
from apps.properties.serializers import AdminPropertySerializer
from .models import TableUnit


class MGAPublicationPolicy:
    version = "mga-publication-1.0"
    review_warnings = {
        "OCR_REQUER_CONFERENCIA", "UNIDADE_NAO_DISPONIVEL",
        "UNIDADE_DUPLICADA_NO_DOCUMENTO", "BAIXA_CONFIANCA_OCR",
        "CONFLITO_FINALIDADE", "CONFLITO_TIPOLOGIA", "PRECO_SUSPEITO",
    }

    def evaluate(self, property):
        from .extraction.service import validation_issues

        issues = []
        origins = list(property.table_origins.select_related("document"))
        if not origins or any(u.document.developer_profile != "mga" for u in origins):
            issues.append("ORIGEM_MGA_NAO_CONFIRMADA")
        for unit in origins:
            if validation_issues(unit):
                issues.append("DADOS_DA_TABELA_PENDENTES")
            if not unit.reviewed and self.review_warnings.intersection(unit.warnings):
                issues.append("CONFERENCIA_DA_TABELA_PENDENTE")
        if not property.valor or property.valor <= 0:
            issues.append("SEM_PRECO")
        if not property.cidade or not property.bairro or not property.logradouro:
            issues.append("ENDERECO_INCOMPLETO")
        if not PublicationPolicy.area(property)[0]:
            issues.append("SEM_AREA")
        if property.tipo == "apartamento" and not (property.quartos or property.suites):
            issues.append("QUARTOS_NAO_IDENTIFICADOS")
        photos = list(property.imagens.all())
        counts = Counter(photo.categoria for photo in photos)
        if not 6 <= len(photos) <= 10:
            issues.append("QUANTIDADE_DE_FOTOS")
        if not counts["fachada"]:
            issues.append("SEM_FACHADA")
        if any(counts[category] > cap for category, cap in (("fachada", 2), ("lazer", 4), ("internos", 3))):
            issues.append("LIMITES_DA_GALERIA")
        order = {"fachada": 0, "lazer": 1, "internos": 2}
        categories = [order.get(photo.categoria, 99) for photo in photos]
        if (99 in categories or categories != sorted(categories) or
                (photos and (photos[0].categoria != "fachada" or not photos[0].imagem_capa)) or
                sum(photo.imagem_capa for photo in photos) != 1):
            issues.append("ORDEM_DA_GALERIA")
        if any(not photo.imagem.storage.exists(photo.imagem.name) for photo in photos):
            issues.append("ARQUIVO_DE_IMAGEM_AUSENTE")
        serializer = AdminPropertySerializer(property, data={"status": "publicado"}, partial=True)
        if not serializer.is_valid():
            issues.append("VALIDACAO_ADMIN")
        return {"policy": self.version, "eligible": not issues, "issues": sorted(set(issues)),
                "photos": len(photos), "counts": dict(counts)}

    def apply(self, property_id):
        with transaction.atomic():
            property = Property.objects.select_for_update().get(pk=property_id)
            # Manual withdrawal, sold/rented status and already public offers win.
            if property.status != Property.Status.RASCUNHO:
                return {"policy": self.version, "published": False, "status": property.status,
                        "decision": "status_preservado"}
            result = self.evaluate(property)
            if result["eligible"]:
                serializer = AdminPropertySerializer(property, data={"status": "publicado"}, partial=True)
                serializer.is_valid(raise_exception=True)
                serializer.save()
            result.update(published=result["eligible"], status=property.status,
                          checked_at=timezone.now().isoformat())
            for unit in TableUnit.objects.select_for_update().filter(imported_property=property):
                unit.evidence = {**unit.evidence, "publication": result}
                unit.save(update_fields=["evidence"])
            return result
