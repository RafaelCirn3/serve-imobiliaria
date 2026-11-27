from collections import Counter
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.properties.models import Property
from apps.robot.publication import MGAPublicationPolicy
from apps.robot.synchronization import MGASynchronizer


class Command(BaseCommand):
    help = "Confere o padrão aprovado MGA; --aplicar publica somente os rascunhos aptos."

    def add_arguments(self, parser):
        parser.add_argument("--aplicar", action="store_true")

    def handle(self, *args, **options):
        started = perf_counter()
        policy = MGAPublicationPolicy()
        rows = []
        properties = Property.objects.filter(status="rascunho", table_origins__document__developer_profile="mga").distinct()
        for property in properties.order_by("pk"):
            result = policy.apply(property.pk) if options["aplicar"] else policy.evaluate(property)
            rows.append({"property_id": property.pk, "project": property.empreendimento, **result})
            self.stdout.write(f"[{perf_counter()-started:.1f}s] Imóvel {property.pk}: {'apto' if result.get('eligible') else 'pendente'}")
        report = {"policy": policy.version, "applied": options["aplicar"],
                  "eligible": sum(bool(row.get("eligible")) for row in rows),
                  "published": sum(bool(row.get("published")) for row in rows),
                  "pending": sum(not row.get("eligible") for row in rows),
                  "issues": dict(Counter(issue for row in rows for issue in row.get("issues", []))), "units": rows}
        MGASynchronizer.checkpoint(settings.BASE_DIR / "reports/mga/publication-policy.json", report)
        self.stdout.write(f"[{perf_counter()-started:.1f}s] {report['eligible']} aptos; {report['published']} publicados; {report['pending']} pendentes.")
