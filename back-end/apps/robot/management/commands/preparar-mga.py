"""Replay verified tables into drafts, preserving manually reviewed data."""

import json
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from apps.robot.extraction.document import DocumentExtractor
from apps.robot.extraction.service import inspect_table, commit_unit
from apps.robot.models import TableImport, TableUnit
from apps.robot.profiles import normalize


class Command(BaseCommand):
    help = "Recupera rodapé, andar e tipologia de tabelas MGA já capturadas e cadastra unidades válidas como rascunhos."

    def add_arguments(self, parser):
        parser.add_argument("--empreendimento", required=True)
        parser.add_argument("--contexto", type=Path)
        parser.add_argument("--aplicar", action="store_true")
        images = parser.add_mutually_exclusive_group()
        images.add_argument("--vincular-imagens", action="store_true", default=True, help="Vincula imagens por padrão")
        images.add_argument("--sem-imagens", dest="vincular_imagens", action="store_false", help="Adia imagens explicitamente")
        parser.add_argument("--output", type=Path, default=settings.BASE_DIR / "reports/mga/preparacao.json")

    def handle(self, *args, **options):
        started = perf_counter()
        context = json.loads(options["contexto"].read_text(encoding="utf-8-sig")) if options["contexto"] else {}
        report = {"created": 0, "existing": 0, "pending": [], "updated_candidates": 0, "documents": [], "groups": []}
        properties = []
        for document in TableImport.objects.filter(developer_profile="mga"):
            if normalize(document.context.get("empreendimento", "")) != normalize(options["empreendimento"]):
                continue
            path = settings.BASE_DIR / f"reports/mga/input/{document.drive_file_id}.pdf"
            self.stdout.write(f"[{perf_counter() - started:.1f}s] Lendo tabela e rodapé: {document.filename}")
            result = inspect_table(path.read_bytes(), document.filename, {**document.context, **context},
                extractor=DocumentExtractor(settings.BASE_DIR / "reports/mga/cache"))
            if result["content_sha256"] != document.content_sha256:
                raise CommandError("O PDF mudou; revise a versão antes de atualizar candidatos.")
            fresh = {}
            for row in result["units"]:
                key = (row["fields"]["unidade"], row["fields"]["torre"])
                fresh.setdefault(key, []).append(row)
            report["documents"].append({"id": str(document.pk), "context": result["context"], "parser": result["parser_version"]})
            for unit in document.units.order_by("index"):
                rows = fresh.get((unit.fields["unidade"], unit.fields["torre"]), [])
                if len(rows) != 1:
                    report["pending"].append({"unit_id": unit.pk, "reason": "Identidade ambígua"})
                    continue
                row = rows[0]
                if unit.reviewed:
                    report["pending"].append({"unit_id": unit.pk, "reason": "Revisão manual preservada"})
                    continue
                if options["aplicar"]:
                    with transaction.atomic():
                        unit = TableUnit.objects.select_for_update().get(pk=unit.pk)
                        before = unit.fields
                        # A published property's price remains untouched.
                        unit.fields, unit.warnings = row["fields"], row["warnings"]
                        unit.evidence = {**unit.evidence, **{k:v for k,v in row.items() if k != "fields"},
                            "metadata_refresh": [*unit.evidence.get("metadata_refresh", []),
                                {"at": timezone.now().isoformat(), "before": before, "parser": result["parser_version"]}]}
                        unit.save(update_fields=["fields", "warnings", "evidence"])
                        if unit.imported_property_id:
                            property = unit.imported_property
                            for field in ("andar", "tipologia", "previsao_entrega", "registro_incorporacao", "area_total", "area_privativa"):
                                current, value = getattr(property, field), unit.fields.get(field)
                                repeated_floor = field == "andar" and current and value and set(str(current).split()) == {str(value)}
                                if value and (not current or current == before.get(field) or repeated_floor):
                                    setattr(property, field, unit.fields[field])
                            property.save()
                    try:
                        property, created = commit_unit(unit.pk, with_images=options["vincular_imagens"])
                        report["created" if created else "existing"] += 1
                        properties.append(property)
                    except ValidationError as exc:
                        report["pending"].append({"unit_id": unit.pk, "issues": exc.detail})
                report["updated_candidates"] += 1
        if not report["documents"]:
            raise CommandError("Empreendimento não encontrado nas tabelas capturadas.")
        groups = {}
        for property in properties:
            groups.setdefault(property.grupo_publicacao, []).append(property)
        from apps.properties.publications import PublicationPolicy
        report["groups"] = [{"title": PublicationPolicy.title(rows[0]), "count":len(rows),
                             "min_price":str(min(prices)) if prices else None}
                            for rows in groups.values()
                            for prices in [[p.valor for p in rows if p.valor is not None and p.valor > 0]]]
        report["duration_seconds"] = round(perf_counter() - started, 3)
        options["output"].parent.mkdir(parents=True, exist_ok=True)
        options["output"].write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        self.stdout.write(f"[{report['duration_seconds']}s] {report['created']} rascunhos criados; {report['existing']} existentes; {len(report['pending'])} pendentes; {len(groups)} grupos. Nenhum status de publicação alterado.")
