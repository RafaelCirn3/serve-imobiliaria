from pathlib import Path
import json
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from rest_framework.exceptions import ValidationError

from apps.robot.extraction.document import DocumentExtractor, ExtractionError, MAX_BYTES
from apps.robot.extraction.service import commit_unit, inspect_table, stage_table, validation_issues
from apps.robot.inventory import read_inventory
from apps.robot.mapping import annotate_inventory
from apps.robot.sources import DEFAULT_SOURCES
from apps.robot.profile_defaults import COMPANIES


class Command(BaseCommand):
    help = "MVP MGA: texto primeiro, OCR local se necessário; prévia, candidatos ou rascunhos idempotentes."

    def add_arguments(self, parser):
        group = parser.add_mutually_exclusive_group(required=True)
        group.add_argument("--arquivo", type=Path)
        group.add_argument("--inventario", type=Path)
        parser.add_argument("--baixar", action="store_true", help="Baixa somente as tabelas MGA selecionadas no inventário")
        parser.add_argument("--contexto", type=Path, help="JSON de campos verificados: default e projects, ou um objeto simples")
        parser.add_argument("--empreendimento", default="")
        parser.add_argument("--salvar", action="store_true", help="Persiste candidatos para revisão")
        parser.add_argument("--aplicar", action="store_true", help="Persiste candidatos e importa unidades válidas como rascunho")
        parser.add_argument("--sem-ocr", action="store_true")
        parser.add_argument("--cache-dir", type=Path, default=settings.BASE_DIR / "reports" / "mga" / "cache")
        parser.add_argument("--input-dir", type=Path, default=settings.BASE_DIR / "reports" / "mga" / "input")
        parser.add_argument("--output", type=Path, default=settings.BASE_DIR / "reports" / "mga" / "resultado.json")

    def handle(self, *args, **options):
        started = perf_counter()

        def progress(message):
            if options["verbosity"]:
                self.stdout.write(f"[{perf_counter() - started:.1f}s] {message}")
                self.stdout.flush()

        try:
            context_config = json.loads(options["contexto"].read_text(encoding="utf-8-sig")) if options["contexto"] else {}
            if not isinstance(context_config, dict):
                raise ValueError("Contexto deve ser um objeto JSON.")
            items = []
            if options["arquivo"]:
                if options["arquivo"].stat().st_size > MAX_BYTES:
                    raise ExtractionError("Arquivo maior que 15 MB.")
                items = [{"path": options["arquivo"], "name": options["arquivo"].name, "project": options["empreendimento"], "id": "", "source_id": ""}]
            else:
                for source, folders, files in read_inventory(options["inventario"]):
                    if source.pasta_id != DEFAULT_SOURCES[1][1]:
                        continue
                    annotate_inventory(source, folders, files)
                    for file in files:
                        if file["classification"].get("categoria") == "tabela_precos" and not file["classification"]["excluido"]:
                            items.append({"path": options["input_dir"] / (file["id"] + ".pdf"), "name": file["name"],
                                          "id": file["id"], "project": file.get("project_identity", {}).get("name", ""), "source_id": source.pasta_id,
                                          "builders": file.get("project_identity", {}).get("companies", [])})
            if not items:
                raise ExtractionError("Nenhuma tabela MGA encontrada.")
            if options["inventario"] and options["aplicar"]:
                from apps.robot.gallery import index_images

                progress(f"{index_images(options['inventario'])} imagens categorizadas preparadas para os imóveis.")
            extractor = DocumentExtractor(options["cache_dir"], progress)
            summary = {"documents": [], "errors": [], "created": 0, "existing": 0, "pending": 0, "mapped": 0}
            for item in items:
                progress(f"Tabela: {item['name']}")
                try:
                    if options["baixar"] and item["id"]:
                        self.download(item, progress)
                    if item["path"].stat().st_size > MAX_BYTES:
                        raise ExtractionError("Arquivo maior que 15 MB.")
                    context = {**context_config.get("default", {}), **context_config.get("projects", {}).get(item["project"], {})} if "default" in context_config or "projects" in context_config else dict(context_config)
                    if item["project"]:
                        context.setdefault("empreendimento", item["project"])
                    if item.get("builders"):
                        names = {company.key: company.name for company in COMPANIES}
                        context.setdefault("construtora", " / ".join(names.get(key, key) for key in item["builders"]))
                    result = inspect_table(item["path"].read_bytes(), item["name"], context, allow_ocr=not options["sem_ocr"], extractor=extractor)
                    report = {key: value for key, value in result.items() if key != "pages"}
                    report["page_methods"] = [{"page": page["number"], "method": page["method"]} for page in result["pages"]]
                    summary["mapped"] += len(result["units"])
                    if options["salvar"] or options["aplicar"]:
                        document, _ = stage_table(result, source_folder_id=item["source_id"], drive_file_id=item["id"])
                        report["document_id"] = str(document.pk)
                        report["unit_results"] = []
                        for unit in document.units.order_by("index"):
                            outcome = {"unit_id": unit.pk, "issues": validation_issues(unit)}
                            if not options["aplicar"] and (outcome["issues"] or unit.warnings):
                                summary["pending"] += 1
                            if options["aplicar"]:
                                try:
                                    property, created = commit_unit(unit.pk)
                                    summary["created" if created else "existing"] += 1
                                    outcome.update(property_id=property.pk, created=created, status=property.status)
                                except ValidationError as exc:
                                    summary["pending"] += 1
                                    outcome["issues"] = exc.detail
                            report["unit_results"].append(outcome)
                    else:
                        summary["pending"] += sum(bool(unit["warnings"]) for unit in result["units"])
                    summary["documents"].append(report)
                    progress(f"{len(result['units'])} unidade(s) mapeada(s).")
                except (OSError, ExtractionError) as exc:
                    summary["errors"].append({"file": item["name"], "error": str(exc)})
                    self.stderr.write(f"Tabela não processada: {item['name']} ({type(exc).__name__}).")
            summary["duration_seconds"] = round(perf_counter() - started, 3)
            options["output"].parent.mkdir(parents=True, exist_ok=True)
            options["output"].write_text(json.dumps(summary, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
            progress(f"Resultado: {options['output'].resolve()}; {summary['created']} rascunho(s) criado(s), {summary['existing']} existente(s), {summary['pending']} pendente(s).")
            if summary["errors"]:
                raise CommandError(f"Execução parcial: {len(summary['errors'])} tabela(s) com falha. Consulte o JSON.")
        except (OSError, ValueError) as exc:
            raise CommandError(str(exc)) from None

    def download(self, item, progress):
        from io import BytesIO
        from googleapiclient.http import MediaIoBaseDownload
        from apps.robot.drive import drive_service

        buffer = BytesIO()
        try:
            service = drive_service()
            download = MediaIoBaseDownload(buffer, service.files().get_media(fileId=item["id"], supportsAllDrives=True), chunksize=1024 * 1024)
            done = False
            while not done:
                _, done = download.next_chunk(num_retries=2)
                if buffer.tell() > MAX_BYTES:
                    raise ExtractionError("Download da tabela excede 15 MB.")
        except ExtractionError:
            raise
        except Exception as exc:
            raise ExtractionError(f"Falha no download ({type(exc).__name__}); confira acesso à fonte.") from None
        item["path"].parent.mkdir(parents=True, exist_ok=True)
        item["path"].write_bytes(buffer.getvalue())
        progress("Tabela baixada para processamento local.")
