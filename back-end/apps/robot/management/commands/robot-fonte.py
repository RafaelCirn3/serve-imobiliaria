import json
from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.robot.developer_pipeline import JOBS, run_job
from apps.robot.extraction.document import ExtractionError


class Command(BaseCommand):
    help = "Processa uma fonte configurada pelo motor compartilhado, com conferência de cobertura e rascunhos."
    developer_profile = None

    def add_arguments(self, parser):
        if self.developer_profile is None:
            parser.add_argument("--perfil", choices=sorted(JOBS), required=True)
        parser.add_argument("--arquivo", type=Path, required=True)
        parser.add_argument("--inventory", type=Path, required=True)
        parser.add_argument("--output", type=Path)
        parser.add_argument("--aplicar", action="store_true")
        parser.add_argument("--image-cache", type=Path)

    def handle(self, *args, **options):
        profile = self.developer_profile or options["perfil"]
        try:
            report = run_job(JOBS[profile], json.loads(options["inventory"].read_text(encoding="utf-8")),
                             options["arquivo"].read_bytes(), base_dir=settings.BASE_DIR,
                             apply=options["aplicar"], image_cache=options["image_cache"], progress=self.stdout.write)
        except (ExtractionError, OSError, ValueError) as exc:
            raise CommandError(str(exc)) from None
        output = options["output"] or settings.BASE_DIR / f"reports/{profile}/result.json"
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        self.stdout.write(f"{len(report['extraction']['units'])} unidades mapeadas; {len(report['properties'])} cadastros; "
                          f"{len(report['excluded_units'])} indisponíveis; {len(report['pending'])} pendências de validação.")
