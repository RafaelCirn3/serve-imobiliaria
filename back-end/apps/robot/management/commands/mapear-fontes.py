from pathlib import Path
from types import SimpleNamespace

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils import timezone

from apps.robot.drive import drive_service, scan_source
from apps.robot.models import DriveSource
from apps.robot.report import write_inventory
from apps.robot.sources import DEFAULT_SOURCES


class Command(BaseCommand):
    help = "Mapeia recursivamente as fontes do Google Drive e gera uma planilha XLSX. Execução manual."

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path, help="Caminho do arquivo XLSX de saída")
        parser.add_argument("--source", help="ID da pasta raiz de uma fonte específica")

    def handle(self, *args, **options):
        try:
            sources = list(DriveSource.objects.filter(ativa=True))
        except DatabaseError:
            self.stderr.write("Banco de dados indisponível; usando as duas fontes padrão para este mapeamento.")
            sources = [SimpleNamespace(pk=None, nome=name, pasta_id=folder_id) for name, folder_id in DEFAULT_SOURCES]
        if options["source"]:
            sources = [source for source in sources if source.pasta_id == options["source"]]
        if not sources:
            raise CommandError("Nenhuma fonte ativa encontrada. Confira o cadastro de fontes ou --source.")
        try:
            service = drive_service()
            inventories = [(source, *scan_source(service, source)) for source in sources]
        except Exception as exc:
            raise CommandError(f"Falha ao mapear as fontes; nenhuma planilha parcial foi gravada: {exc}") from exc
        timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
        output = options["output"] or settings.BASE_DIR / "reports" / f"mapa-fontes-{timestamp}.xlsx"
        if output.suffix.lower() != ".xlsx":
            raise CommandError("O arquivo de saída deve ter extensão .xlsx.")
        try:
            write_inventory(output, inventories)
        except OSError as exc:
            raise CommandError(f"Não foi possível gravar a planilha: {exc}") from exc
        folders = sum(len(items[1]) for items in inventories)
        files = sum(len(items[2]) for items in inventories)
        self.stdout.write(self.style.SUCCESS(f"{len(sources)} fonte(s), {folders} pasta(s), {files} arquivo(s): {output.resolve()}"))
