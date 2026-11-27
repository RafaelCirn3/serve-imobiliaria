"""Shared local workflow: verify source bytes, extract, reconcile, stage and attach galleries."""
from collections import Counter
from dataclasses import dataclass
import hashlib
import re
from pathlib import Path
from types import SimpleNamespace

from .extraction.document import DocumentExtractor, ExtractionError
from .extraction.service import inspect_table, stage_table, commit_unit, validation_issues
from .gallery import index_inventories, attach_images, download_image
from .mapping import annotate_inventory
from .models import DriveSource


@dataclass(frozen=True)
class DeveloperJob:
    profile: str
    source_id: str
    table_id: str
    book_id: str
    context: dict


JOBS = {
    "setai": DeveloperJob("setai", "1oyftGZQJ2PljwIyhiipsc2kuFsyW02rg", "1OuEDeciuLh6aBWXMeqoJlprjlhWysRhB",
        "1gxhEebYP9FVOlcIOs5-lhaKRT7i8DFFf", {"empreendimento": "SETAI Sandro Barros", "cidade": "João Pessoa",
        "bairro": "Cabo Branco", "tipo": "apartamento", "finalidade": "venda", "construtora": "SETAI / Grupo GP Exclusive",
        "endereco": "Av. Cabo Branco, nº 2860"}),
    "icon": DeveloperJob("icon", "1xwjaaLOZVu3fstFeS2XNAYOwNtIRFMjr", "1XIQOUsqnVajYGY1GjqOz-PIGkZ4I835B",
        "1SgD0mYllMftdiUiTA5CTQIkV15rslMR7", {"empreendimento": "MOSS", "cidade": "João Pessoa", "bairro": "Cabo Branco",
        "tipo": "flat", "finalidade": "venda", "construtora": "ICON", "endereco": "Av. Monsenhor Odilon Coutinho"}),
}


def description(fields, raw):
    area_text = "Área não informada na tabela. "
    for field, label in (("area_total", "Área total informada"), ("area_privativa", "Área privativa informada"),
                         ("area_informada", "Área informada")):
        if fields.get(field):
            area_text = f"{label}: {fields[field]} m². "
            break
    return (
        f"{fields['empreendimento']}, unidade {fields['unidade']}, {fields.get('bairro', '')}, {fields.get('cidade', '')}/PB. "
        f"{area_text}"
        f"Preço extraído da tabela de {raw.get('data_tabela') or 'data não identificada'}. "
        "Vigência do preço e disponibilidade da unidade pendentes de confirmação. "
        "Imagens ilustrativas do empreendimento e de apartamentos decorados; "
        "não comprovam a mobília ou o acabamento desta unidade. Cadastro em revisão."
    )


def reconcile_units(result):
    """Compare extraction with independent counts printed in the DWV document."""
    text = "\n".join(page["text"] for page in result["pages"])
    available = re.search(r"(\d+)\s+unidades?\s+dispon[ií]veis", text, re.I)
    unavailable = re.search(r"(\d+)\s+unidades?\s+indispon[ií]veis", text, re.I)
    parsed = Counter(u["raw"].get("situacao_comercial", "nao_informada") for u in result["units"])
    declared = {"available": int(available[1]), "unavailable": int(unavailable[1])} if available and unavailable else None
    matched = (len(result["units"]) == sum(declared.values()) and parsed["disponivel"] == declared["available"]
               and sum(v for k, v in parsed.items() if k != "disponivel") == declared["unavailable"]) if declared else None
    return {"declared": declared, "extracted": len(result["units"]), "statuses": dict(parsed), "matched": matched}


def run_job(job, snapshot, content, *, base_dir, apply=False, image_cache=None, progress=None):
    progress = progress or (lambda message: None)
    source = SimpleNamespace(**snapshot["source"])
    if source.pasta_id != job.source_id:
        raise ExtractionError("A fonte do inventário não corresponde ao perfil selecionado.")
    files = snapshot["files"]
    table = next((f for f in files if f["id"] == job.table_id), None)
    book = next((f for f in files if f["id"] == job.book_id), None)
    if not table or not book or table["mime_type"] != "application/pdf":
        raise ExtractionError("Tabela ou book do empreendimento ausentes no inventário.")
    if not table.get("md5_checksum") or hashlib.md5(content).hexdigest() != table["md5_checksum"]:
        raise ExtractionError("O PDF não corresponde ao checksum da tabela inventariada no Drive.")
    if apply:
        configured = DriveSource.objects.filter(pasta_id=source.pasta_id).first()
        if configured:
            source.perfil = configured.perfil
    annotate_inventory(source, snapshot["folders"], files)
    result = inspect_table(content, table["name"], job.context, developer_profile=job.profile,
                           extractor=DocumentExtractor(Path(base_dir) / f"reports/{job.profile}/cache", progress))
    if not result["units"]:
        raise ExtractionError("Layout não reconhecido; nenhum cadastro foi alterado.")
    reconciliation = reconcile_units(result)
    if job.profile == "icon" and reconciliation["matched"] is not True:
        raise ExtractionError("A extração não corresponde às contagens declaradas na tabela ICON; importação bloqueada.")
    for unit in result["units"]:
        unit["raw"]["book_drive_id"] = job.book_id
        unit["raw"]["context_evidence"] = {"cidade_bairro_tipo": "book", "endereco_area": "tabela" if job.profile == "setai" else "book_e_tabela"}
        unit["fields"]["descricao"] = description(unit["fields"], unit["raw"])
    report = {"profile": job.profile, "extraction": result, "applied": apply, "properties": [], "pending": [],
              "excluded_units": [{"index": index, "unidade": u["fields"]["unidade"], "reason": "UNIDADE_NAO_DISPONIVEL"}
                                 for index, u in enumerate(result["units"], 1) if "UNIDADE_NAO_DISPONIVEL" in u["warnings"]],
              "reconciliation": reconciliation,
              "inventory": {"source_id": source.pasta_id, "folders": len(snapshot["folders"]), "files": len(files),
                            "classification": dict(Counter(f["classification"]["status_decisao"] for f in files)),
                            "categories": dict(Counter(f["classification"]["categoria"] for f in files if f["classification"]["categoria"])),
                            "unclassified": [{"id": f["id"], "name": f["name"], "reason": f["classification"]["motivo"]}
                                             for f in files if not f["classification"]["categoria"] and not f["classification"]["excluido"]]}}
    metadata_by_id = {f["id"]: f for f in files}

    def download(asset):
        if image_cache:
            path = Path(image_cache) / f"{asset.file_id}.jpg"
            expected = metadata_by_id.get(asset.file_id, {}).get("md5_checksum")
            if path.exists() and expected:
                data = path.read_bytes()
                if hashlib.md5(data).hexdigest() == expected:
                    return data
        return download_image(asset)

    if apply:
        report["indexed_images"] = index_inventories([(source, snapshot["folders"], files)])
        document, _ = stage_table(result, source_folder_id=source.pasta_id, drive_file_id=job.table_id)
        report["document_id"] = str(document.pk)
        for unit in document.units.order_by("index"):
            if "UNIDADE_NAO_DISPONIVEL" in unit.warnings:
                continue
            issues = validation_issues(unit)
            if issues:
                report["pending"].append({"unit": unit.pk, "issues": issues})
                continue
            property, created = commit_unit(unit.pk, with_images=False)
            if property.status == "rascunho" and not unit.reviewed:
                unit.fields["descricao"] = result["units"][unit.index - 1]["fields"]["descricao"]
                unit.save(update_fields=["fields"])
                property.descricao = unit.fields["descricao"]
                property.save(update_fields=["descricao", "atualizado_em"])
            gallery = attach_images(unit.pk, downloader=download, progress=progress)
            report["properties"].append({"id": property.pk, "created": created, "unidade": property.unidade,
                                       "valor": str(property.valor), "status": property.status,
                                       "photos": property.imagens.count(), "gallery": gallery})
            progress(f"Unidade {property.unidade}: {property.status}, {property.imagens.count()} fotos.")
    return report
