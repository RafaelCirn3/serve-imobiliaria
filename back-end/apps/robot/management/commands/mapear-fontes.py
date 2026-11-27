from pathlib import Path
from time import perf_counter
from types import SimpleNamespace
from uuid import uuid4
import hashlib

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import DatabaseError
from django.utils import timezone

from apps.robot.drive import drive_service, scan_source
from apps.robot.models import DriveSource
from apps.robot.report import write_inventory
from apps.robot.sources import DEFAULT_SOURCES
from apps.robot.inventory import read_inventory, read_rule_snapshot
from apps.robot.mapping import annotate_inventory
from apps.robot.profiles import ENGINE_VERSION


class Command(BaseCommand):
    help = "Mapeia todas as pastas e arquivos das fontes ativas, sem excluir materiais pelos filtros, e gera XLSX."
    output_prefix = "mapa-fontes"
    preparation_label = "Organização do inventário completo"

    @staticmethod
    def format_duration(seconds):
        tenths = int(seconds * 10)
        hours, remainder = divmod(tenths, 36000)
        minutes, remainder = divmod(remainder, 600)
        seconds, fraction = divmod(remainder, 10)
        return f"{hours:02}:{minutes:02}:{seconds:02}.{fraction}"

    def progress(self, message):
        if self.verbosity > 0:
            elapsed = self.format_duration(perf_counter() - self.started_at)
            self.stdout.write(f"[{elapsed}] {message}")
            self.stdout.flush()

    def prepare_inventory(self, source, folders, files):
        return source, folders, files

    def write_report(self, output, inventories, execution):
        write_inventory(output, inventories)

    def finalize_report(self, execution):
        pass

    def add_arguments(self, parser):
        parser.add_argument("--output", type=Path, help="Caminho do arquivo XLSX de saída")
        parser.add_argument("--source", help="ID da pasta raiz de uma fonte específica")
        parser.add_argument("--input-inventory", type=Path, help="Replay offline de um inventário XLSX completo, sem banco ou Drive")
        parser.add_argument("--strict", action="store_true", help="Interrompe na primeira falha de fonte, sem gravar relatório parcial")
        parser.add_argument("--rules-from", type=Path, help="Usa a configuração da aba Regras de um relatório V2 anterior")

    def handle(self, *args, **options):
        self.started_at = perf_counter()
        self.verbosity = options["verbosity"]
        self.execution = {"run_id": str(uuid4()), "started_at": timezone.localtime().isoformat(), "errors": [], "partial": False,
                          "engine_version": ENGINE_VERSION, "input_inventory": str(options.get("input_inventory") or "Google Drive")}
        self.raw_inventories = []
        self.report_written = False
        self.progress(f"Início do mapeamento: {self.output_prefix}.")
        succeeded = False
        try:
            self.run_mapping(options)
            succeeded = True
        finally:
            self.execution.update(finished_at=timezone.localtime().isoformat(), duration_seconds=round(perf_counter() - self.started_at, 3), success=succeeded)
            if self.report_written:
                self.finalize_report(self.execution)
            status = "Concluído parcialmente" if succeeded and self.execution["partial"] else "Concluído" if succeeded else "Interrompido"
            self.progress(f"{status} — tempo total de execução.")

    def run_mapping(self, options):
        if options.get("output") and options.get("input_inventory") and options["output"].resolve() == options["input_inventory"].resolve():
            raise CommandError("O relatório de saída não pode sobrescrever o inventário de entrada.")
        if options.get("output") and options["output"].suffix.lower() != ".xlsx":
            raise CommandError("O arquivo de saída deve ter extensão .xlsx.")
        self.progress("Carregando fontes ativas.")
        replay = None
        if options.get("input_inventory"):
            try:
                replay = {source.pasta_id: (source, folders, files) for source, folders, files in read_inventory(options["input_inventory"])}
                self.execution["input_sha256"] = hashlib.sha256(options["input_inventory"].read_bytes()).hexdigest()
            except (OSError, ValueError, KeyError) as exc:
                raise CommandError(f"Inventário offline inválido: {type(exc).__name__}.") from None
            sources = [entry[0] for entry in replay.values()]
        else:
            try:
                sources = list(DriveSource.objects.filter(ativa=True))
            except DatabaseError:
                self.stderr.write(f"Banco de dados indisponível; usando as {len(DEFAULT_SOURCES)} fontes padrão para este mapeamento.")
                sources = [SimpleNamespace(pk=None, nome=name, pasta_id=folder_id) for name, folder_id in DEFAULT_SOURCES]
        if options["source"]:
            sources = [source for source in sources if source.pasta_id == options["source"]]
        if not sources:
            raise CommandError("Nenhuma fonte ativa encontrada. Confira o cadastro de fontes ou --source.")
        if options.get("rules_from"):
            try:
                configs = read_rule_snapshot(options["rules_from"])
                for source in sources:
                    source.perfil = configs[source.pasta_id]
            except (OSError, ValueError, KeyError) as exc:
                raise CommandError(f"Snapshot de regras inválido ou incompleto ({type(exc).__name__}).") from None
            self.execution["rules_from"] = str(options["rules_from"])
        self.progress(f"{len(sources)} fonte(s) selecionada(s). " + ("Replay offline, sem acesso ao Drive." if replay is not None else "Conectando ao Google Drive."))
        try:
            service = None if replay is not None else drive_service()
            self.progress("Inventário local preparado." if replay is not None else "Conexão com o Google Drive preparada.")
            inventories = []
            for index, source in enumerate(sources, start=1):
                started = perf_counter()
                label = f"Fonte {index}/{len(sources)}: {source.nome} ({source.pasta_id})"
                self.progress(f"{label} — iniciando consulta.")
                try:
                    if replay is not None:
                        _, folders, files = replay[source.pasta_id]
                        annotate_inventory(source, folders, files)
                    else:
                        folders, files = scan_source(service, source)
                    self.raw_inventories.append((source, folders, files))
                except Exception as exc:
                    from apps.robot.drive import DriveAccessError

                    message = str(exc) if isinstance(exc, DriveAccessError) else type(exc).__name__
                    self.execution["errors"].append({"source_id": source.pasta_id, "error": message})
                    self.execution["partial"] = True
                    self.stderr.write(f"{label} — falha: {message}. Fonte poderá ser reprocessada com --source.")
                    if options["strict"]:
                        raise CommandError("Falha de fonte em modo estrito; nenhuma planilha parcial foi gravada.") from None
                    self.raw_inventories.append((source, [], []))
                    inventories.append((source, [], []))
                    continue
                duration = self.format_duration(perf_counter() - started)
                self.progress(f"{label} — consulta finalizada em {duration}: {len(folders)} pasta(s), {len(files)} arquivo(s).")
                self.progress(f"{label} — {self.preparation_label}.")
                inventory = self.prepare_inventory(source, folders, files)
                inventories.append(inventory)
                duration = self.format_duration(perf_counter() - started)
                self.progress(f"{label} — pronta em {duration}: {len(inventory[1])} pasta(s), {len(inventory[2])} arquivo(s) no relatório.")
        except CommandError:
            raise
        except Exception as exc:
            raise CommandError(f"Falha ao preparar o mapeamento ({type(exc).__name__}); nenhuma planilha parcial foi gravada.") from None
        if len(self.execution["errors"]) == len(sources):
            raise CommandError("Todas as fontes falharam; nenhuma planilha foi gravada.")
        timestamp = timezone.localtime().strftime("%Y%m%d-%H%M%S")
        output = options["output"] or settings.BASE_DIR / "reports" / f"{self.output_prefix}-{timestamp}.xlsx"
        if output.suffix.lower() != ".xlsx":
            raise CommandError("O arquivo de saída deve ter extensão .xlsx.")
        try:
            started = perf_counter()
            self.progress(f"Gravando planilha: {output.resolve()}.")
            self.execution.update(finished_at=timezone.localtime().isoformat(), duration_seconds=round(perf_counter() - self.started_at, 3))
            self.write_report(output, inventories, self.execution)
            self.report_written = True
            self.progress(f"Planilha gravada em {self.format_duration(perf_counter() - started)}.")
        except OSError as exc:
            raise CommandError(f"Não foi possível gravar a planilha: {exc}") from exc
        folders = sum(len(items[1]) for items in inventories)
        files = sum(len(items[2]) for items in inventories)
        self.stdout.write(self.style.SUCCESS(f"{len(sources)} fonte(s), {folders} pasta(s), {files} arquivo(s): {output.resolve()}"))
        if self.execution["partial"]:
            self.stderr.write(f"EXECUÇÃO PARCIAL: {len(self.execution['errors'])} fonte(s) com falha. Consulte a auditoria e reexecute com --source.")
