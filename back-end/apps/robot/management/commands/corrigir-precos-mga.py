from pathlib import Path
import json
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.robot.extraction.document import DocumentExtractor
from apps.robot.extraction.mga import decimal_br
from apps.robot.extraction.service import inspect_table
from apps.robot.models import TableImport, TableUnit
from apps.robot.profiles import normalize


def identity(fields):
    return tuple(normalize(fields.get(key, "")) for key in ("empreendimento", "torre", "unidade"))


class Command(BaseCommand):
    help = "Reconfere preços MGA com o PDF, preservando anúncios e revisões manuais."

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true")
        parser.add_argument("--input-dir", type=Path, default=settings.BASE_DIR / "reports/mga/input")
        parser.add_argument("--cache-dir", type=Path, default=settings.BASE_DIR / "reports/mga/cache")
        parser.add_argument("--output", type=Path, default=settings.BASE_DIR / "reports/mga/correcao-precos.json")

    def handle(self, *args, **options):
        started = perf_counter()
        report = {"applied": options["aplicar"], "changes": [], "blocked": [], "errors": []}
        for document in TableImport.objects.filter(developer_profile="mga"):
            path = options["input_dir"] / f"{document.drive_file_id}.pdf"
            self.stdout.write(f"[{perf_counter() - started:.1f}s] Conferindo {document.filename}")
            try:
                result = inspect_table(path.read_bytes(), document.filename, document.context,
                                       extractor=DocumentExtractor(options["cache_dir"]))
                if result["content_sha256"] != document.content_sha256:
                    raise ValueError("PDF difere do hash original; requer revisão de versão.")
                candidates = {}
                for candidate in result["units"]:
                    candidates.setdefault(identity(candidate["fields"]), []).append(candidate)
                with transaction.atomic():
                    for unit in TableUnit.objects.select_for_update().filter(document=document):
                        matches = candidates.get(identity(unit.fields), [])
                        if len(matches) != 1:
                            report["blocked"].append({"unit_id": unit.pk, "reason": "Identidade ausente ou ambígua"})
                            continue
                        new = matches[0]
                        value = new["fields"].get("valor")
                        if value == unit.fields.get("valor"):
                            continue
                        change = {"unit_id": unit.pk, "document": document.filename,
                                  "unit": unit.fields.get("unidade"), "tower": unit.fields.get("torre"),
                                  "before": unit.fields.get("valor"), "after": value, "page": new["page"]}
                        raw_value = decimal_br(unit.evidence.get("raw", {}).get("valor"))
                        if unit.reviewed or unit.imported_property_id or not value or raw_value != unit.fields.get("valor") or "PRECO_SUSPEITO" in new["warnings"]:
                            report["blocked"].append({**change, "reason": "Anúncio/revisão existente ou preço sem evidência segura"})
                            continue
                        report["changes"].append(change)
                        if options["aplicar"]:
                            unit.fields = {**unit.fields, "valor": value}
                            history = unit.evidence.get("price_corrections", [])
                            unit.evidence = {**unit.evidence, "raw": new["raw"], "price_corrections": [*history,
                                {**change, "at": timezone.now().isoformat(), "parser": result["parser_version"]}]}
                            unit.warnings = [w for w in unit.warnings if w not in ("CAMPO_PENDENTE:valor", "PRECO_SUSPEITO")]
                            unit.save(update_fields=["fields", "evidence", "warnings"])
            except (OSError, ValueError) as exc:
                report["errors"].append({"document": document.filename, "error": str(exc)})
        report["duration_seconds"] = round(perf_counter() - started, 3)
        options["output"].parent.mkdir(parents=True, exist_ok=True)
        options["output"].write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f"[{report['duration_seconds']}s] {len(report['changes'])} correções; {len(report['blocked'])} bloqueios; {len(report['errors'])} erros.")
        if report["errors"]:
            raise CommandError("Conferência parcial; consulte o relatório.")
