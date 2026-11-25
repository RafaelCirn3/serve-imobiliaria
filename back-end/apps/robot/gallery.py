"""Galerias sortidas por metadados; nenhuma vistoria semântica das imagens."""

from collections import Counter
import hashlib
from io import BytesIO
from urllib.parse import urlparse
import random
import re
import secrets

from django.conf import settings
from django.db import transaction
from django.db.models import Q

from apps.common.images import prepare_images
from apps.properties.models import Property, PropertyImage
from .inventory import read_inventory
from .mapping import annotate_inventory
from .models import DriveImageAsset, DriveSource, PropertyImageSelection, TableUnit
from .profiles import normalize
from .sources import DEFAULT_SOURCES

CATEGORY_ORDER = ("fachada", "lazer", "internos")
CAPS = {"fachada": 2, "lazer": 4, "internos": 3}
MAX_IMAGE_BYTES = 64 * 1024 * 1024


def project_identity(name):
    # Apenas sufixos de localização explícitos, sem correspondência aproximada.
    return normalize(re.sub(r"\s*\([^)]*(?:Bananeiras|João Pessoa|Cabedelo|\bPB\b)[^)]*\)\s*$", "", name, flags=re.I))


def index_images(path):
    inventories = read_inventory(path)
    configured = {source.pasta_id: source.perfil for source in DriveSource.objects.all()}
    assets, sources = [], []
    for source, folders, files in inventories:
        source.perfil = configured.get(source.pasta_id, {})
        sources.append(source.pasta_id)
        annotate_inventory(source, folders, files)
        for item in files:
            classification = item.get("classification", {})
            identity = item.get("project_identity", {})
            if classification.get("categoria") not in CAPS or classification.get("excluido") or not identity.get("name"):
                continue
            assets.append(DriveImageAsset(source_id=source.pasta_id, file_id=item["id"], folder_id=item["folder_id"], name=item["name"],
                path=item["folder_path"], mime_type=item["mime_type"], project_name=identity["name"],
                project_normalized=project_identity(identity["name"]), category=classification["categoria"], url=item["url"],
                metadata={"classification": classification, "identity": identity, "size": item.get("size"), "modified_time": item.get("modified_time", ""),
                          "avulso": "avulsos" in normalize(item["folder_path"], metadata=True)}, active=True))
    with transaction.atomic():
        DriveImageAsset.objects.filter(source_id__in=sources).update(active=False)
        DriveImageAsset.objects.bulk_create(assets, update_conflicts=True, unique_fields=["source_id", "file_id"],
            update_fields=["folder_id", "name", "path", "mime_type", "project_name", "project_normalized", "category", "url", "metadata", "active"])
    return len(assets)


def scoped_assets(unit):
    property = unit.imported_property
    source_id = unit.document.source_folder_id or DEFAULT_SOURCES[1][1]
    name = project_identity(property.empreendimento)
    assets = list(DriveImageAsset.objects.filter(active=True, source_id=source_id, project_normalized=name).order_by("file_id"))
    document_text = unit.document.filename + " " + " ".join(page.get("text", "") for page in unit.document.extraction.get("pages", []))
    avulso = "avulsos" in normalize(document_text, metadata=True)
    related_units = set()
    if avulso:
        for candidate in TableUnit.objects.filter(document__developer_profile=unit.document.developer_profile,
                document__source_folder_id__in=[source_id, ""]).values_list("fields", flat=True):
            if project_identity(candidate.get("empreendimento", "")) == name:
                related_units.add((normalize(candidate.get("unidade", "")), normalize(candidate.get("torre", ""))))
    selected = []
    for asset in assets:
        if avulso != bool(asset.metadata.get("avulso")):
            continue
        text = normalize(asset.path + " " + asset.name, metadata=True)
        # Nunca utilizar interiores explicitamente associados a outra unidade.
        identifiers = re.findall(r"\b(?:apto|apt|apartamento|unidade|loja|sala|lote)\s*(\d{1,5})\b(?!\s*m2)", text)
        own_numbers = re.findall(r"\d+", property.unidade)
        if identifiers and not set(identifiers).issubset(set(own_numbers)):
            continue
        towers = re.findall(r"\b(?:torre|bloco)\s+([a-z0-9]+)\b", text)
        if towers and normalize(property.torre) not in towers:
            continue
        blocks = re.findall(r"\bquadra\s*([a-z0-9]+)\b", text)
        own_blocks = re.findall(r"\bquadra\s*([a-z0-9]+)\b", normalize(property.unidade))
        if blocks and not set(blocks).issubset(set(own_blocks)):
            continue
        if avulso and len(related_units) > 1 and not identifiers:
            # Mesmo prédio com vários avulsos: pasta genérica não prova vínculo.
            continue
        if avulso and identifiers:
            matches = [(number, tower) for number, tower in related_units
                       if set(identifiers).issubset(set(re.findall(r"\d+", number)))
                       and (not towers or tower in towers)
                       and (not blocks or set(blocks).issubset(set(re.findall(r"\bquadra\s*([a-z0-9]+)\b", number))))]
            if len(matches) > 1:
                continue
        types = re.findall(r"\b(\d+)\s*(quartos|suites)\b", text)
        if asset.category == "internos" and any(int(number) != getattr(property, "quartos" if kind == "quartos" else "suites") for number, kind in types):
            continue
        selected.append(asset)
    return selected


def build_plan(assets, seed, peer_sequences=()):
    if peer_sequences:
        # Sample alternatives from this property's eligible inventory only.
        # Lexicographic scoring avoids identical galleries, then repeated covers
        # and positions. Never borrow another project's pictures for diversity.
        lookup = {asset.pk: asset.file_id for asset in assets}
        covers = Counter(sequence[0] for sequence in peer_sequences if sequence)
        def score(plan):
            sequence = tuple(lookup[pk] for category in CATEGORY_ORDER
                             for pk in plan["pools"][category][:plan["quotas"][category]])
            return (sequence in peer_sequences, covers[sequence[0]] if sequence else 0,
                    sum(sum(a == b for a, b in zip(sequence, peer)) for peer in peer_sequences))
        candidates = [build_plan(assets, seed + offset) for offset in range(128)]
        plan = min(candidates, key=score)
        plan["diversity"] = "acervo_sem_variacao" if score(plan)[0] else "sequencia_distinta"
        return plan
    rng = random.Random(seed)
    pools = {category: [] for category in CATEGORY_ORDER}
    seen = set()
    for asset in assets:
        if asset.file_id not in seen:
            pools[asset.category].append(asset.pk)
            seen.add(asset.file_id)
    for category in CATEGORY_ORDER:
        rng.shuffle(pools[category])
    capacity = {category: min(CAPS[category], len(pools[category])) for category in CATEGORY_ORDER}
    available = sum(capacity.values())
    target = rng.randint(6, available) if available >= 6 else available
    quotas = {"fachada": min(capacity["fachada"], target), "lazer": 0, "internos": 0}
    while sum(quotas.values()) < target:
        choices = [category for category in ("lazer", "internos") if quotas[category] < capacity[category]]
        quotas[rng.choice(choices)] += 1
    return {"version": "gallery-2.0", "target": target, "quotas": quotas, "pools": pools}


def peer_sequences(property):
    companies = [name.strip() for name in property.construtora.split("/") if name.strip()]
    if not companies:
        return []
    query = Q()
    for company in companies:
        query |= Q(construtora__icontains=company)
    peers = Property.objects.filter(query).exclude(pk=property.pk).exclude(status=Property.Status.INATIVO).prefetch_related("imagens").select_related("robot_gallery").order_by("pk")
    identities = {normalize(name) for name in companies}
    sequences = []
    for peer in peers:
        if not identities.intersection(normalize(name.strip()) for name in peer.construtora.split("/")):
            continue
        sequence = tuple(photo.origem_drive_id for photo in peer.imagens.all() if photo.origem_drive_id)
        if not sequence:
            # A committed plan reserves its sequence before downloads complete.
            selection = getattr(peer, "robot_gallery", None)
            plan = selection.plan if selection else {}
            ids = [pk for category in CATEGORY_ORDER for pk in plan.get("pools", {}).get(category, [])[:plan.get("quotas", {}).get(category, 0)]]
            lookup = dict(DriveImageAsset.objects.filter(pk__in=ids).values_list("pk", "file_id"))
            sequence = tuple(lookup[pk] for pk in ids if pk in lookup)
        if sequence:
            sequences.append(sequence)
    return sequences


def download_image(asset):
    from googleapiclient.http import MediaIoBaseDownload
    from .drive import drive_service, execute

    if not re.fullmatch(r"[A-Za-z0-9_-]{10,128}", asset.file_id):
        raise ValueError("ID de imagem inválido.")
    version = hashlib.sha256(asset.metadata.get("modified_time", "").encode()).hexdigest()[:12]
    cache = settings.BASE_DIR / "reports" / "image-cache" / (asset.file_id + "-" + version + ".bin")
    if cache.exists():
        if cache.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Imagem acima de 64 MB.")
        return cache.read_bytes()
    service = drive_service()
    if (asset.metadata.get("size") or 0) > 10 * 1024 * 1024:
        metadata = execute(service.files().get(fileId=asset.file_id, fields="thumbnailLink,capabilities(canDownload)", supportsAllDrives=True))
        link = metadata.get("thumbnailLink", "")
        parsed = urlparse(link)
        if metadata.get("capabilities", {}).get("canDownload") is not False and parsed.scheme == "https" and (parsed.hostname or "").endswith(".googleusercontent.com"):
            # Rendição do próprio arquivo fornecida pelo Drive, baixada no servidor;
            # o link temporário nunca é exposto na galeria ou persistido no banco.
            link = re.sub(r"=s\d+(?:-[A-Za-z0-9]+)*$", "=s2560", link)
            try:
                response, content = service._http.request(link, method="GET")
                if response.status == 200 and len(content) <= MAX_IMAGE_BYTES:
                    cache.parent.mkdir(parents=True, exist_ok=True)
                    cache.write_bytes(content)
                    asset.metadata = {**asset.metadata, "rendition": "drive_thumbnail_2560"}
                    asset.save(update_fields=["metadata"])
                    return content
            except Exception:
                pass  # O download normal abaixo mantém a mesma validação/limite.
    if (asset.metadata.get("size") or 0) > MAX_IMAGE_BYTES:
        raise ValueError("Imagem acima de 64 MB.")
    output = BytesIO()
    downloader = MediaIoBaseDownload(output, service.files().get_media(fileId=asset.file_id, supportsAllDrives=True), chunksize=4 * 1024 * 1024)
    done = False
    while not done:
        _, done = downloader.next_chunk(num_retries=2)
        if output.tell() > MAX_IMAGE_BYTES:
            raise ValueError("Imagem acima de 64 MB.")
    cache.parent.mkdir(parents=True, exist_ok=True)
    cache.write_bytes(output.getvalue())
    return output.getvalue()


def attach_images(unit_id, downloader=None, progress=None):
    unit = TableUnit.objects.select_related("document", "imported_property").get(pk=unit_id)
    if not unit.imported_property_id:
        return {"status": "aguardando_importacao"}
    property = unit.imported_property
    if property.imagens.filter(origem_drive_id="").exists():
        return {"status": "imagens_manuais_preservadas"}
    assets = scoped_assets(unit)
    selection, _ = PropertyImageSelection.objects.get_or_create(property=property, defaults={"seed": secrets.randbits(63)})
    with transaction.atomic():
        # Serialize planning for this developer to reserve different sequences
        # even when two imports run concurrently.
        if property.construtora:
            list(Property.objects.filter(construtora=property.construtora).order_by("pk").select_for_update().values_list("pk", flat=True))
        selection = PropertyImageSelection.objects.select_for_update().get(pk=selection.pk)
        if not selection.plan or selection.plan.get("target", 0) < 6 or selection.plan.get("version") != "gallery-2.0":
            selection.plan = build_plan(assets, selection.seed, peer_sequences(property))
            selection.save(update_fields=["plan", "updated_at"])
    lookup = {asset.pk: asset for asset in assets}
    errors = []
    attempts = 0
    progress = progress or (lambda message: None)
    downloader = downloader or download_image
    for category in CATEGORY_ORDER:
        if len(errors) >= 6:
            break
        for asset_id in selection.plan["pools"][category]:
            if property.imagens.filter(categoria=category).count() >= selection.plan["quotas"][category]:
                break
            asset = lookup.get(asset_id)
            if asset is None or property.imagens.filter(origem_drive_id=asset.file_id).exists():
                continue
            if attempts >= selection.plan["target"] + 6:
                break
            attempts += 1
            stored = None
            try:
                from django.core.files.base import ContentFile

                progress(f"Imóvel {property.pk} — {category}: consultando imagem {asset.file_id}.")
                raw = downloader(asset)
                image = prepare_images([ContentFile(raw, name=asset.name)], max_input_bytes=MAX_IMAGE_BYTES, decoder_thumbnail=True)[0]
                digest = hashlib.sha256(image.read()).hexdigest()
                image.seek(0)
                with transaction.atomic():
                    Property.objects.select_for_update().get(pk=property.pk)
                    if property.imagens.filter(conteudo_sha256=digest).exists() or property.imagens.filter(categoria=category).count() >= selection.plan["quotas"][category]:
                        continue
                    photo = PropertyImage(imovel=property, categoria=category, origem_drive_id=asset.file_id,
                        origem_drive_url=asset.url, origem_pasta_id=asset.folder_id, conteudo_sha256=digest,
                        vistoria_pendente=True, legenda={"fachada": "Fachada", "lazer": "Área de lazer", "internos": "Ambientes internos"}[category])
                    photo.imagem.save(image.name, image, save=False)
                    stored = photo.imagem
                    photo.save()
            except Exception as exc:
                if stored:
                    stored.delete(save=False)
                errors.append({"file_id": asset.file_id, "error": type(exc).__name__})
                if len(errors) >= 6:
                    break
    with transaction.atomic():
        Property.objects.select_for_update().get(pk=property.pk)
        photos = list(property.imagens.all())
        if any(not photo.origem_drive_id for photo in photos):
            return {"status": "imagens_manuais_preservadas"}
        positions = {lookup[pk].file_id: index for category in CATEGORY_ORDER
                     for index, pk in enumerate(selection.plan["pools"][category]) if pk in lookup}
        photos.sort(key=lambda photo: (CATEGORY_ORDER.index(photo.categoria), positions.get(photo.origem_drive_id, 100000), photo.pk))
        for index, photo in enumerate(photos):
            PropertyImage.objects.filter(pk=photo.pk).update(ordem=index, imagem_capa=index == 0)
        counts = dict(Counter(photo.categoria for photo in photos))
        warnings = [f"SEM_{category.upper()}" for category in CATEGORY_ORDER if not counts.get(category)]
        if len(photos) < 6:
            warnings.append("ACERVO_INSUFICIENTE_MINIMO_6")
        if tuple(photo.origem_drive_id for photo in photos) in peer_sequences(property):
            warnings.append("ACERVO_SEM_VARIACAO_DE_SEQUENCIA")
        result = {"status": "vinculado" if len(photos) >= 6 else "incompleto" if photos else "aguardando_acervo", "total": len(photos), "counts": counts,
                  "warnings": warnings, "errors": errors, "vistoria_pendente": True, "avulso_escopo": "pasta_do_proprio_imovel"}
        selection.result = result
        selection.save(update_fields=["result", "updated_at"])
        return result


def attach_after_commit(unit_id):
    """A falha de imagens não desfaz o imóvel já importado."""
    try:
        attach_images(unit_id)
    except Exception as exc:
        unit = TableUnit.objects.get(pk=unit_id)
        selection, _ = PropertyImageSelection.objects.get_or_create(property_id=unit.imported_property_id, defaults={"seed": secrets.randbits(63)})
        selection.result = {"status": "pendente", "error": type(exc).__name__}
        selection.save(update_fields=["result", "updated_at"])
