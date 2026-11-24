from collections import defaultdict

from django.utils import timezone

from .drive import drive_service, scan_source
from .models import DrivePublication, DriveSource


def sync_sources(service=None):
    """Cria uma divulgação pendente por pasta de empreendimento com arquivos.

    Preço, endereço e tipo de imóvel não são inferidos de nomes de arquivos.
    A revisão editorial ocorre antes de qualquer cadastro público de imóvel.
    """
    service = service or drive_service()
    created = updated = 0
    for source in DriveSource.objects.filter(ativa=True):
        folders, files = scan_source(service, source)
        folders_by_id = {folder["id"]: folder for folder in folders}
        by_project = defaultdict(list)
        for item in files:
            by_project[item["project_id"]].append({
                "id": item["id"], "nome": item["name"], "caminho": item["folder_path"],
                "tipo_mime": item["mime_type"], "url": item["url"],
                "modificado_em": item["modified_time"],
            })
        for project_id, assets in by_project.items():
            folder = folders_by_id[project_id]
            assets.sort(key=lambda item: (item["caminho"].casefold(), item["nome"].casefold(), item["id"]))
            defaults = {
                "titulo": folder["name"][:180], "caminho": folder["path"],
                "url_pasta": folder["url"], "arquivos": assets,
            }
            publication, was_created = DrivePublication.objects.get_or_create(
                fonte=source, pasta_id=project_id, defaults=defaults
            )
            if was_created:
                created += 1
            elif any(getattr(publication, field) != value for field, value in defaults.items()):
                for field, value in defaults.items():
                    setattr(publication, field, value)
                publication.save(update_fields=[*defaults, "atualizada_em"])
                updated += 1
        source.ultima_consulta_em = timezone.now()
        source.save(update_fields=["ultima_consulta_em"])
    return {"criadas": created, "atualizadas": updated}
