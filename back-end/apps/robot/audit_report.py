"""Relatório V2: partição de decisões, evidências e configurações reproduzíveis."""

from collections import Counter, defaultdict
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from xml.etree import ElementTree as ET
from zipfile import ZipFile

from .mapping import audit_duplicates
from .profiles import ENGINE_VERSION, get_profile, normalize
from .report import add_sheet, atomic_save, inventory_book

CATEGORIES = ("tabela_precos", "fachada", "lazer", "internos")
TRACE_HEADERS = ["source_id", "drive_file_id", "drive_folder_id", "nome_original", "nome_normalizado", "caminho_original", "mime_type",
                 "categoria_principal", "tags_secundarias", "empreendimento_original", "empreendimento_canonico", "origem_material", "construtora",
                 "regra_aplicada", "palavra_chave_encontrada", "segmento_correspondente", "evidencias", "motivo_selecao", "motivo_exclusao",
                 "confianca_categoria", "confianca_empreendimento", "confianca_construtora", "requer_revisao", "motivos_revisao", "status_decisao", "versao_motor",
                 "conversao_necessaria", "situacao_comercial", "elegivel_anuncio", "md5_checksum", "sha256_checksum", "dimensoes_imagem", "segmentos_contextuais",
                 "confianca_categoria_detalhes", "confianca_empreendimento_detalhes", "confianca_construtora_detalhes", "vigencia", "datas_comerciais", "modified_time",
                 "incorporadora", "unidade_contexto_original", "fonte_drive"]


def compact(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def candidate(item):
    classification = item.get("classification", {})
    return bool(classification.get("categoria") and not classification.get("excluido"))


def trace_row(source, item):
    import re

    c, identity = item["classification"], item.get("project_identity", {})
    profile = get_profile(source)
    evidence = c.get("evidencias", [])
    project_confidence, developer_confidence = identity.get("project_confidence", {}), identity.get("developer_confidence", {})
    return [source.pasta_id, item["id"], item["folder_id"], item["name"], normalize(item["name"]), item["folder_path"], item["mime_type"],
            c["categoria"], compact(c.get("tags", [])), identity.get("original", ""), identity.get("name", ""), profile.config["origin"] if profile else source.nome,
            compact(identity.get("developers", identity.get("companies", []))), compact(c.get("regras", [])), compact([e["palavra"] for e in evidence]), compact([e["segmento"] for e in evidence]),
            compact(evidence), c["motivo"] if candidate(item) else "", c["motivo"] if c["excluido"] else "",
            c.get("pontuacao", 0), project_confidence.get("pontuacao", 0), developer_confidence.get("pontuacao", 0), c["revisao"], compact(c.get("motivos_revisao", [])),
            c["status_decisao"], ENGINE_VERSION, c.get("requires_conversion", False), c.get("situacao_comercial", "nao_confirmada"), c.get("elegivel_anuncio", False),
            item.get("md5_checksum", ""), item.get("sha256_checksum", ""), compact(item.get("image_metadata", {})), compact(item.get("path_segments", [])),
            compact(c.get("confianca_categoria", {})), compact(project_confidence), compact(developer_confidence), c.get("vigencia", ""),
            compact(re.findall(r"\d{4}[.-]\d{2}|\d{2}[- /]\d{2}[- /]\d{4}|\d{2}[_-]\d{4}", item["folder_path"] + "/" + item["name"])), item.get("modified_time", ""),
            compact(identity.get("incorporators", [])), compact(item.get("unit_context", [])), f"https://drive.google.com/drive/folders/{source.pasta_id}"]


def metrics(inventories):
    files = [item for _, _, items in inventories for item in items]
    selected = [item for item in files if candidate(item)]
    decisions = Counter(item["classification"]["status_decisao"] for item in files)
    return {"fontes": len(inventories), "pastas": sum(len(folders) for _, folders, _ in inventories), "originais": len(files),
            "candidatos": len(selected), "nao_candidatos": len(files) - len(selected),
            "selecionados": decisions["SELECIONADO"], "descartados": decisions["DESCARTADO"], "revisao": decisions["REVISAO"],
            "bytes_originais": sum(item.get("size") or 0 for item in files), "bytes_candidatos": sum(item.get("size") or 0 for item in selected),
            **dict(Counter(item["classification"]["categoria"] for item in selected))}


def write_filter_report(path, inventories, execution):
    selected_inventories = [(source, folders, [item for item in files if candidate(item)]) for source, folders, files in inventories]
    book = inventory_book(selected_inventories)
    discarded, review, trace_selected = [], [], []
    projects, coverage = {}, defaultdict(set)
    source_metrics = {}
    for source, folders, files in inventories:
        source_metrics[source.pasta_id] = metrics([(source, folders, files)])
        for item in files:
            row = trace_row(source, item)
            c, identity = item["classification"], item.get("project_identity", {})
            if candidate(item):
                trace_selected.append(row)
            if c["status_decisao"] == "DESCARTADO":
                discarded.append(row)
            if c["status_decisao"] == "REVISAO":
                review.append(row)
            key = identity.get("key") or f"unresolved:{source.pasta_id}"
            entry = projects.setdefault(key, {"identity": identity, "sources": set(), "situations": set()})
            entry["sources"].add(source.pasta_id)
            entry["situations"].add(c.get("situacao_comercial", "nao_confirmada"))
            if candidate(item):
                coverage[key].add(c["categoria"])

    # As 18 colunas iniciais permanecem compatíveis com o relatório V1.
    sheet = book["Arquivos"]
    for column, label in enumerate(TRACE_HEADERS, start=19):
        sheet.cell(1, column, label)
    trace_lookup = {(row[0], row[1]): row for row in trace_selected}
    ordered_keys = [(source.pasta_id, item["id"]) for source, _, files in selected_inventories
                    for item in sorted(files, key=lambda item: (item["folder_path"].casefold(), item["name"].casefold()))]
    for cells, key in zip(sheet.iter_rows(min_row=2, max_col=18), ordered_keys, strict=True):
        row = trace_lookup[key]
        for column, value in enumerate(row, start=19):
            from .report import safe_text
            sheet.cell(cells[0].row, column, safe_text(value))
    from .report import add_sheet as styled_sheet
    # Reutiliza o estilo existente para todas as colunas de rastreabilidade.
    rows = list(sheet.iter_rows(min_row=2, values_only=True))
    headers = [cell.value for cell in sheet[1]]
    book.remove(sheet)
    styled_sheet(book, "Arquivos", headers, rows, [34, 65, 45, 42, 20, 25, 43, 43, 55] + [30] * (len(headers) - 9), 9)
    for title, rows in (("Descartados", discarded), ("Revisão", review)):
        add_sheet(book, title, TRACE_HEADERS, rows, [30] * len(TRACE_HEADERS))

    summary = metrics(inventories)
    headers = ["Originais", "Candidatos (inclui revisão)", "Selecionados sem revisão", "Descartados", "Em revisão", "Bytes originais", "Bytes candidatos", "Redução arquivos", "Redução bytes", "Versão motor", *CATEGORIES]
    sheet = book["Resumo"]
    for j, label in enumerate(headers, start=5):
        sheet.cell(1, j, label)
    for i, (source, _, _) in enumerate(inventories, start=2):
        values = source_metrics[source.pasta_id]
        extend_summary(sheet, i, values)
    extend_summary(sheet, len(inventories) + 2, summary)

    sheet = book["Fontes"]
    extra = ["Originais", "Candidatos", "Descartados", "Em revisão", "Retenção candidatos", "Falha acesso", *CATEGORIES]
    errors = {e["source_id"]: e["error"] for e in execution.get("errors", [])}
    for j, label in enumerate(extra, start=8):
        sheet.cell(1, j, label)
    for i, (source, _, _) in enumerate(inventories, start=2):
        m = source_metrics[source.pasta_id]
        for j, value in enumerate([m["originais"], m["candidatos"], m["descartados"], m["revisao"], m["candidatos"] / m["originais"] if m["originais"] else 0,
                                   errors.get(source.pasta_id, ""), *[m.get(c, 0) for c in CATEGORIES]], start=8):
            sheet.cell(i, j, value)
        sheet.cell(i, 12).number_format = "0.0%"

    ordered_folders = [folder for _, folders, _ in inventories for folder in sorted(folders, key=lambda item: item["path"].casefold())]
    sheet = book["Pastas"]
    for j, label in enumerate(("Tipo estrutural", "Empreendimento", "Regra agrupamento", "Categoria presumida"), start=10):
        sheet.cell(1, j, label)
    for cells, folder in zip(sheet.iter_rows(min_row=2, max_col=9), ordered_folders, strict=True):
        for j, value in enumerate((folder.get("structural_role", ""), folder.get("project_name", ""), folder.get("grouping_rule", ""), folder.get("category", "")), start=10):
            from .report import safe_text
            sheet.cell(cells[0].row, j, safe_text(value))

    project_rows, coverage_rows = [], []
    for key, entry in sorted(projects.items()):
        identity = entry["identity"]
        project_rows.append([key, identity.get("name", ""), compact(identity.get("aliases", [])), compact(identity.get("companies", [])),
                             compact(identity.get("related_companies", [])), compact(sorted(entry["sources"])), identity.get("project_confidence", {}).get("pontuacao", 0), compact(sorted(entry["situations"]))])
        coverage_rows.append([key, identity.get("name", ""), *[category in coverage[key] for category in CATEGORIES], len(coverage[key]) / 4, "Cobertura documental; não comprova disponibilidade"])
    add_sheet(book, "Empreendimentos", ["Chave", "Empreendimento", "Aliases", "Construtoras", "Empresas relacionadas", "Fontes", "Confiança empreendimento", "Situação comercial"], project_rows, [45, 40, 55, 30, 35, 60, 25, 40])
    add_sheet(book, "Cobertura", ["Chave", "Empreendimento", *CATEGORIES, "Cobertura", "Observação"], coverage_rows, [45, 40, 22, 18, 18, 18, 18, 65])
    for cell in book["Cobertura"]["G"][1:]:
        cell.number_format = "0%"
    duplicates = audit_duplicates(inventories)
    add_sheet(book, "Duplicidades", ["Nível", "Chave", "Origens preservadas", "Decisão", "Hash de conteúdo", "Hash perceptual", "Referência preferencial", "Critério (sem inspeção visual)"],
              [[r["kind"], r["key"], compact(r["references"]), r["decision"], "Não calculado; checksum do Drive quando disponível", "Etapa futura", compact(r["preferred"]),
                "Relevância, ausência de promoção, formato web e resolução informada; não confirma qualidade visual"] for r in duplicates], [20, 60, 100, 50, 55, 25, 65, 100])
    configs = {source.pasta_id: get_profile(source).config if get_profile(source) else {} for source, _, _ in inventories}
    config_hash = hashlib.sha256(compact(configs).encode()).hexdigest()
    add_sheet(book, "Regras", ["source_id", "Versão", "SHA256 configuração", "Configuração efetiva JSON"],
              [[key, ENGINE_VERSION, hashlib.sha256(compact(value).encode()).hexdigest(), compact(value)] for key, value in sorted(configs.items())], [45, 20, 70, 120])
    audit = {**execution, "engine_version": ENGINE_VERSION, "rules_sha256": config_hash, "processed": summary["originais"],
             "decisions_reconcile": summary["originais"] == summary["selecionados"] + summary["descartados"] + summary["revisao"],
             "semantics": "Arquivos=candidatos categorizados; Revisão é uma visão complementar. Status principal particiona o universo sem dupla contagem.",
             "size_limitation": "Tamanhos ausentes tratados como desconhecidos; volumes somam somente bytes conhecidos; checksums não existem no XLSX V1."}
    add_sheet(book, "Auditoria", ["Campo", "Valor"], [[key, compact(value) if isinstance(value, (dict, list)) else value] for key, value in audit.items()], [38, 120])
    # Reaplica estilo às abas que receberam colunas extras.
    for title in ("Resumo", "Fontes", "Pastas"):
        sheet = book[title]
        headers = [cell.value for cell in sheet[1]]
        rows = list(sheet.iter_rows(min_row=2, values_only=True))
        index = book.index(sheet)
        book.remove(sheet)
        add_sheet(book, title, headers, rows, [35] + [25] * (len(headers) - 1))
        book._sheets.insert(index, book._sheets.pop())
    for row in book["Resumo"].iter_rows(min_row=2):
        for column in (12, 13):
            row[column - 1].number_format = "0.0%"
    for cell in book["Fontes"]["L"][1:]:
        cell.number_format = "0.0%"
    # Preserva a posição das abas originais.
    order = ["Resumo", "Fontes", "Pastas", "Arquivos", "Descartados", "Revisão", "Empreendimentos", "Cobertura", "Duplicidades", "Regras", "Auditoria"]
    book._sheets = [book[title] for title in order]
    atomic_save(book, path)
    return summary


def extend_summary(sheet, row, m):
    values = [m["originais"], m["candidatos"], m["selecionados"], m["descartados"], m["revisao"], m["bytes_originais"], m["bytes_candidatos"],
              1 - m["candidatos"] / m["originais"] if m["originais"] else 0, 1 - m["bytes_candidatos"] / m["bytes_originais"] if m["bytes_originais"] else 0,
              ENGINE_VERSION, *[m.get(category, 0) for category in CATEGORIES]]
    for column, value in enumerate(values, start=5):
        sheet.cell(row, column, value)


def finalize_execution_audit(path, execution):
    """Atualiza apenas a aba de auditoria após XLSX, amostra e comparativo.

    Evita reconstruir todas as células com Openpyxl. A troca do ZIP é atômica;
    data/duração representam o fechamento da auditoria, antes deste commit final.
    """
    ns = "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
    rel_ns = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
    path = Path(path)
    temporary = None
    try:
        with ZipFile(path) as original:
            workbook = ET.fromstring(original.read("xl/workbook.xml"))
            relation_id = next(sheet.attrib[f"{{{rel_ns}}}id"] for sheet in workbook.find(f"{{{ns}}}sheets") if sheet.attrib["name"] == "Auditoria")
            relationships = ET.fromstring(original.read("xl/_rels/workbook.xml.rels"))
            target = next(rel.attrib["Target"] for rel in relationships if rel.attrib["Id"] == relation_id)
            target = target.lstrip("/") if target.startswith("/") else "xl/" + target
            sheet = ET.fromstring(original.read(target))
            data = sheet.find(f"{{{ns}}}sheetData")
            values = {}
            for row in list(data)[1:]:
                cells = list(row)
                key = "".join(cells[0].itertext())
                values[key] = row
            for key in ("finished_at", "duration_seconds", "success"):
                value = execution[key]
                row = values.get(key)
                if row is None:
                    index = len(data) + 1
                    row = ET.SubElement(data, f"{{{ns}}}row", r=str(index))
                    cell = ET.SubElement(row, f"{{{ns}}}c", r=f"A{index}", t="inlineStr")
                    ET.SubElement(ET.SubElement(cell, f"{{{ns}}}is"), f"{{{ns}}}t").text = key
                    ET.SubElement(row, f"{{{ns}}}c", r=f"B{index}")
                cell = list(row)[1]
                for child in list(cell):
                    cell.remove(child)
                if isinstance(value, (int, float)):
                    cell.set("t", "b" if isinstance(value, bool) else "n")
                    ET.SubElement(cell, f"{{{ns}}}v").text = str(int(value)) if isinstance(value, bool) else str(value)
                else:
                    cell.set("t", "inlineStr")
                    ET.SubElement(ET.SubElement(cell, f"{{{ns}}}is"), f"{{{ns}}}t").text = value
            dimension = sheet.find(f"{{{ns}}}dimension")
            dimension.set("ref", f"A1:B{len(data)}")
            auto_filter = sheet.find(f"{{{ns}}}autoFilter")
            if auto_filter is not None:
                auto_filter.set("ref", f"A1:B{len(data)}")
            with NamedTemporaryFile(dir=path.parent, suffix=".xlsx", delete=False) as handle:
                temporary = Path(handle.name)
            with ZipFile(temporary, "w") as replacement:
                for entry in original.infolist():
                    payload = ET.tostring(sheet, encoding="utf-8") if entry.filename == target else original.read(entry.filename)
                    replacement.writestr(entry, payload, compress_type=entry.compress_type, compresslevel=1)
        os.replace(temporary, path)
    finally:
        if temporary and temporary.exists():
            temporary.unlink()
