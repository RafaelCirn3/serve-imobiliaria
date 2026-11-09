"""Read-only diagnosis of records pointing to missing media files."""
import json
from django.core.management.base import BaseCommand
from apps.properties.models import PropertyImage
from apps.banners.models import Banner
from apps.banners.section_image import SectionImage
from apps.locations.models import Region
from apps.leads.models import LeadImage


class Command(BaseCommand):
    help = 'Verifica arquivos de imagens cadastradas, sem alterar o banco ou apagar arquivos.'

    def add_arguments(self, parser):
        parser.add_argument('--json', action='store_true', help='Retorna diagnóstico estruturado.')

    def handle(self, *args, **options):
        report = {'verificados': 0, 'ausentes': [], 'falhas_armazenamento': []}
        for model, field in [(PropertyImage, 'imagem'), (Banner, 'imagem'), (SectionImage, 'image'), (Region, 'imagem'), (LeadImage, 'imagem')]:
            for record in model.objects.all().iterator():
                image = getattr(record, field)
                if not image:
                    continue
                report['verificados'] += 1
                item = {'modelo': model._meta.label, 'id': record.pk, 'arquivo': image.name}
                try:
                    if not image.storage.exists(image.name):
                        report['ausentes'].append(item)
                except OSError as error:
                    report['falhas_armazenamento'].append({**item, 'erro': type(error).__name__})
        if options['json']:
            self.stdout.write(json.dumps(report, ensure_ascii=False))
        else:
            self.stdout.write(f"{report['verificados']} arquivo(s) verificado(s); {len(report['ausentes'])} ausente(s); {len(report['falhas_armazenamento'])} falha(s) de armazenamento.")
            for item in report['ausentes'] + report['falhas_armazenamento']:
                self.stdout.write(f"{item['modelo']} #{item['id']}: {item['arquivo']}")
