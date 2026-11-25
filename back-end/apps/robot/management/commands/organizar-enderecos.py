import json
from pathlib import Path
from time import perf_counter

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.serializers.json import DjangoJSONEncoder

from apps.locations.addressing import AddressNormalizer
from apps.locations.resolution import AddressResolver
from apps.properties.models import Property
from apps.robot.models import TableUnit


class Command(BaseCommand):
    help = "Organiza endereços do robô, consulta CEP e geocodifica mantendo posição aproximada."

    def add_arguments(self, parser):
        parser.add_argument("--empreendimento")
        parser.add_argument("--aplicar", action="store_true")
        parser.add_argument("--area-total", action="store_true", help="Adota a área informada como total, por decisão explícita")
        parser.add_argument("--output", type=Path, default=settings.BASE_DIR / "reports/mga/enderecos-organizados.json")

    def handle(self, *args, **options):
        started = perf_counter()
        properties = Property.objects.filter(table_origins__isnull=False).distinct().order_by("pk")
        if options["empreendimento"]:
            properties = properties.filter(empreendimento__iexact=options["empreendimento"])
        report = []
        for index, property in enumerate(properties, 1):
            source = {key: getattr(property, key) for key in ("endereco", "logradouro", "numero", "bairro", "cidade", "uf", "cep", "latitude", "longitude", "localizacao_exata")}
            if options["aplicar"]:
                result = AddressResolver().apply(property)
                property.refresh_from_db()
                if options["area_total"] and property.area_total is None and property.area_informada:
                    property.area_total = property.area_informada
                    property.save(update_fields=["area_total", "atualizado_em"])
                for unit in TableUnit.objects.filter(imported_property=property):
                    unit.evidence = {**unit.evidence, "location_resolution": result, "address_organization": {
                        "before": json.loads(json.dumps(source, cls=DjangoJSONEncoder)), "at": timezone.now().isoformat(), "area_as_total": options["area_total"]}}
                    if options["area_total"] and property.area_total:
                        unit.fields = {**unit.fields, "area_total": str(property.area_total)}
                    unit.save(update_fields=["fields", "evidence"])
            else:
                result = {"fields": AddressNormalizer.parse(source), "warnings": ["PREVIA_SEM_CONSULTA_EXTERNA"]}
            report.append({"property_id": property.pk, **result})
            self.stdout.write(f"[{perf_counter()-started:.1f}s] {index}: imóvel {property.pk}, bairro {result['fields'].get('bairro')}, CEP {result['fields'].get('cep') or 'pendente'}")
        options["output"].parent.mkdir(parents=True, exist_ok=True)
        options["output"].write_text(json.dumps(report, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        self.stdout.write(f"[{perf_counter()-started:.1f}s] {len(report)} endereços organizados; {sum(bool(r['warnings']) for r in report)} com pendências.")
