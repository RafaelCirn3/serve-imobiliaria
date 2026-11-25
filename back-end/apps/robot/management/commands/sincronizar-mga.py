import json
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from apps.robot.synchronization import MGASynchronizer


class Command(BaseCommand):
    help="Sincroniza todas as fontes MGA: inventário, tabelas, imóveis, CEP/localização e galerias."

    def add_arguments(self,parser):
        parser.add_argument("--snapshot",type=Path,help="Retoma inventário completo salvo nesta execução")
        parser.add_argument("--aplicar",action="store_true")
        parser.add_argument("--output",type=Path,default=settings.BASE_DIR/"reports/mga/sync-result.json")

    def handle(self,*args,**options):
        started=perf_counter()
        def progress(message):
            self.stdout.write(f"[{perf_counter()-started:.1f}s] {message}")
            self.stdout.flush()
        engine=MGASynchronizer(progress)
        snapshot=json.loads(options["snapshot"].read_text(encoding="utf-8-sig")) if options["snapshot"] else engine.inventory(settings.BASE_DIR/"reports/mga/sync-inventory-live.json")
        report=engine.run(snapshot,options["output"],apply=options["aplicar"])
        progress(f"Concluído: {report['created']} criados, {report['existing']} existentes, {report['pending']} pendentes; {len(report['errors'])} erros.")
        if report["errors"] or report["source_errors"]:
            raise CommandError("Sincronização parcial. Consulte o relatório e repita para retomar.")
