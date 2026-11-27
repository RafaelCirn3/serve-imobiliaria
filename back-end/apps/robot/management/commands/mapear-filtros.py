from importlib import import_module
from pathlib import Path

from apps.robot.profiles import get_profile
from apps.robot.audit_report import write_filter_report


CompleteMappingCommand = import_module("apps.robot.management.commands.mapear-fontes").Command


class Command(CompleteMappingCommand):
    help = "Mapeia os materiais classificados pelos filtros de cada fonte e gera XLSX, preservando indicações de revisão."
    output_prefix = "mapa-filtros"
    preparation_label = "Aplicação dos filtros da fonte"

    def add_arguments(self, parser):
        super().add_arguments(parser)
        parser.add_argument("--compare-to", type=Path, help="XLSX filtrado V1 para comparação por fonte e ID")
        parser.add_argument("--comparison-output", type=Path, help="Destino do comparativo V1/V2")

    def write_report(self, output, inventories, execution):
        self.summary = write_filter_report(output, self.raw_inventories, execution)
        self.report_path = output
        from apps.robot.quality import write_sample

        sample = output.with_name(output.stem + "-amostra.csv")
        write_sample(sample, self.raw_inventories)
        self.progress(f"Amostra para homologação humana gravada: {sample.resolve()}.")

    def finalize_report(self, execution):
        from apps.robot.audit_report import finalize_execution_audit

        finalize_execution_audit(self.report_path, execution)

    def run_mapping(self, options):
        from django.core.management.base import CommandError

        for output_key in ("output", "comparison_output"):
            if options.get(output_key) and options.get("compare_to") and options[output_key].resolve() == options["compare_to"].resolve():
                raise CommandError("A saída não pode sobrescrever a baseline V1.")
        if options.get("comparison_output") and options["comparison_output"].suffix.lower() != ".xlsx":
            raise CommandError("O arquivo comparativo deve ter extensão .xlsx.")
        super().run_mapping(options)
        if options.get("compare_to"):
            from apps.robot.comparison import write_comparison
            from django.conf import settings

            target = options.get("comparison_output") or settings.BASE_DIR / "reports" / "comparativo-v1-v2.xlsx"
            try:
                write_comparison(target, options["compare_to"], self.raw_inventories)
            except (OSError, ValueError, KeyError) as exc:
                raise CommandError(f"Falha no comparativo: {exc}") from None
            self.progress(f"Comparativo V1/V2 gravado: {target.resolve()}.")

    def prepare_inventory(self, source, folders, files):
        profile = get_profile(source)
        if profile is None:
            self.stderr.write(f"Fonte sem perfil de filtros: {source.nome}. Nenhum material selecionado.")
            for item in files:
                item["classification"] = {"categoria": None, "pontuacao": 0, "revisao": True, "excluido": False,
                                          "motivo": "MISSING_SOURCE_PROFILE", "regras": ["MISSING_SOURCE_PROFILE"],
                                          "motivos_revisao": ["MISSING_SOURCE_PROFILE"], "status_decisao": "REVISAO"}
            return source, folders, []

        selected = []
        for item in files:
            classification = item.get("classification") or profile.classify(item)
            if not classification["excluido"] and classification["categoria"]:
                selected.append({**item, "classification": classification})

        # V2 preserva a hierarquia completa para auditar também os descartes.
        return source, folders, selected
