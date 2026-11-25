import json
from pathlib import Path
from time import perf_counter

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.properties.models import Property
from apps.properties.publications import PublicationPolicy
from apps.robot.models import TableUnit
from apps.robot.profiles import normalize


class Command(BaseCommand):
    help = "Agrupa publicações do robô por construtora, empreendimento, cidade, torre e finalidade; avulsos permanecem individuais."

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true")
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        started = perf_counter()
        report, seen = [], set()
        with transaction.atomic():
            units = TableUnit.objects.filter(imported_property__isnull=False).select_related("document", "imported_property").order_by("imported_property_id")
            for unit in units:
                if unit.imported_property_id in seen:
                    continue
                seen.add(unit.imported_property_id)
                property = Property.objects.select_for_update().get(pk=unit.imported_property_id)
                origins = TableUnit.objects.filter(imported_property=property).select_related("document")
                avulso = any("avulsos" in normalize(origin.document.filename, metadata=True) for origin in origins)
                property.agrupar_publicacao = not avulso
                key = PublicationPolicy.key(property)
                if options["aplicar"]:
                    property.save(update_fields=["agrupar_publicacao", "grupo_publicacao", "atualizado_em"])
                report.append({"property_id": property.pk, "project": property.empreendimento, "tower": property.torre,
                               "group": key, "avulso": avulso, "status": property.status})
        if options["output"]:
            options["output"].parent.mkdir(parents=True, exist_ok=True)
            options["output"].write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f"[{perf_counter() - started:.1f}s] {'Aplicado' if options['aplicar'] else 'Prévia'}: {len(report)} unidades; {len({p['group'] for p in report if p['group']})} grupos; avulsos separados; status preservados.")
