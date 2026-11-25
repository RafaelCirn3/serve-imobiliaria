from pathlib import Path
import json

from django.core.management.base import BaseCommand, CommandError
from apps.robot.gallery import attach_images, build_plan, index_images, scoped_assets
from apps.robot.models import TableUnit


class Command(BaseCommand):
    help = "Indexa imagens filtradas e vincula galerias sortidas aos imóveis importados."

    def add_arguments(self, parser):
        parser.add_argument("--inventario", type=Path, help="Inventário completo para atualizar o catálogo de imagens")
        parser.add_argument("--imovel", type=int, help="Restringir a um imóvel")
        parser.add_argument("--aplicar", action="store_true", help="Baixar e vincular imagens; sem esta opção apenas apresenta prévia")
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        if options["inventario"]:
            total = index_images(options["inventario"])
            self.stdout.write(f"{total} imagens categorizadas indexadas.")
        units = TableUnit.objects.filter(imported_property__isnull=False).select_related("document", "imported_property").order_by("imported_property_id", "pk")
        if options["imovel"]:
            units = units.filter(imported_property_id=options["imovel"])
        results, seen = [], set()
        for unit in units:
            if unit.imported_property_id in seen:
                continue
            seen.add(unit.imported_property_id)
            if options["aplicar"]:
                result = attach_images(unit.pk, progress=self.stdout.write if options["verbosity"] else None)
            else:
                plan = build_plan(scoped_assets(unit), seed=unit.imported_property_id)
                result = {"status": "previa", "counts": plan["quotas"], "total": plan["target"]}
            row = {"imovel_id": unit.imported_property_id, "empreendimento": unit.imported_property.empreendimento, **result}
            results.append(row)
            self.stdout.write(json.dumps(row, ensure_ascii=False))
        if options["output"]:
            options["output"].parent.mkdir(parents=True, exist_ok=True)
            options["output"].write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        if not results:
            self.stdout.write("Nenhum imóvel importado encontrado.")
