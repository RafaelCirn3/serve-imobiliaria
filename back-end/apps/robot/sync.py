from collections import defaultdict
import hashlib
import logging

from django.utils import timezone

from .drive import drive_service, scan_source
from .models import DriveProject, DrivePublication, DriveSource
from .profiles import get_profile


def sync_sources(service=None):
    """Cria uma divulgação pendente por pasta de empreendimento com arquivos.

    Preço, endereço e tipo de imóvel não são inferidos de nomes de arquivos.
    A revisão editorial ocorre antes de qualquer cadastro público de imóvel.
    """
    service = service or drive_service()
    created = updated = 0
    failures = []
    for source in DriveSource.objects.filter(ativa=True):
        profile = get_profile(source)
        try:
            folders, files = scan_source(service, source)
        except Exception as exc:
            # Nunca registrar URL/token nem texto de exceções de bibliotecas.
            failures.append({"source_id": source.pasta_id, "error": type(exc).__name__})
            logging.getLogger(__name__).warning("Falha ao consultar fonte %s (%s)", source.pasta_id, type(exc).__name__)
            continue
        folders_by_id = {folder["id"]: folder for folder in folders}
        by_project = defaultdict(list)
        for item in files:
            if item.get("classification", {}).get("excluido"):
                continue
            identity_key = item.get("project_identity", {}).get("key", "")
            by_project[(item["project_id"], identity_key)].append({
                "id": item["id"], "nome": item["name"], "caminho": item["folder_path"],
                "tipo_mime": item["mime_type"], "url": item["url"],
                "modificado_em": item["modified_time"],
                **({"classificacao": item["classification"], "identidade": item["project_identity"]} if "classification" in item else {}),
            })
        for (project_id, identity_key), assets in by_project.items():
            folder = folders_by_id[project_id]
            assets.sort(key=lambda item: (item.get("classificacao", {}).get("prioridade", 0), item["caminho"].casefold(), item["nome"].casefold(), item["id"]))
            defaults = {
                "titulo": folder["name"][:180], "caminho": folder["path"],
                "url_pasta": folder["url"], "arquivos": assets,
            }
            if identity_key and profile and profile.config["mode"] not in ("complementary", "commercial_only", "avulsos"):
                identity = assets[0]["identidade"]
                project, _ = DriveProject.objects.get_or_create(
                    chave=identity["key"], defaults={"nome": identity["name"][:180],
                    "construtoras": identity["companies"], "confianca": identity["confidence"]},
                )
                defaults.update(empreendimento=project, titulo=identity["name"][:180])
            # Uma pasta de tabelas centralizadas pode conter vários projetos.
            publication_id = project_id
            if identity_key and profile and profile.is_organizational(folder["name"]):
                publication_id = "canonical:" + hashlib.sha256((project_id + identity_key).encode()).hexdigest()[:40]
            publication, was_created = DrivePublication.objects.get_or_create(
                fonte=source, pasta_id=publication_id, defaults=defaults
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
    result = {"criadas": created, "atualizadas": updated}
    if failures:
        result["falhas"] = failures
    return result
