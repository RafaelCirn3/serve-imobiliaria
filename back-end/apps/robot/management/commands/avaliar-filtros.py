import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.robot.quality import evaluate_sample


class Command(BaseCommand):
    help = "Calcula precisão, recall, F1 e matriz de confusão de amostra homologada por humanos."

    def add_arguments(self, parser):
        parser.add_argument("--amostra", type=Path, required=True)
        parser.add_argument("--output", type=Path)

    def handle(self, *args, **options):
        try:
            result = evaluate_sample(options["amostra"])
        except (OSError, ValueError, KeyError) as exc:
            raise CommandError(str(exc)) from None
        text = json.dumps(result, ensure_ascii=False, indent=2)
        if options["output"]:
            options["output"].parent.mkdir(parents=True, exist_ok=True)
            options["output"].write_text(text, encoding="utf-8")
        self.stdout.write(text)
