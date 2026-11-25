"""Planilha de inventário para análise manual das fontes do Drive."""

from collections import Counter
import os
import json
from pathlib import Path
from tempfile import NamedTemporaryFile
from .profiles import get_profile

from openpyxl import Workbook
from openpyxl.cell.cell import ILLEGAL_CHARACTERS_RE
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter


def safe_text(value):
    """Impede que nomes controlados no Drive sejam interpretados como fórmulas."""
    if isinstance(value, str):
        value = ILLEGAL_CHARACTERS_RE.sub("", value)[:32767]
        if value.lstrip().startswith(("=", "+", "-", "@")):
            return "'" + value
    return value


def add_sheet(book, title, headers, rows, widths, link_column=None):
    sheet = book.create_sheet(title)
    sheet.append(headers)
    sheet.freeze_panes = "A2"
    sheet.row_dimensions[1].height = 42
    sheet.sheet_view.showGridLines = False
    for row in rows:
        sheet.append([safe_text(value) for value in row])
    for cell in sheet[1]:
        cell.fill = PatternFill("solid", fgColor="17365D")
        cell.font = Font(color="FFFFFF", bold=True)
        cell.alignment = Alignment(wrap_text=True)
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(vertical="top")
            if cell.row % 2 == 0:
                cell.fill = PatternFill("solid", fgColor="EAF2F8")
        if link_column:
            link = row[link_column - 1]
            if isinstance(link.value, str) and link.value.startswith("https://"):
                link.hyperlink = link.value
                link.font = Font(color="0563C1", underline="single")
    for index, width in enumerate(widths, start=1):
        sheet.column_dimensions[get_column_letter(index)].width = width
    sheet.auto_filter.ref = sheet.dimensions
    return sheet


def inventory_book(inventories):
    book = Workbook()
    book.remove(book.active)
    sources = [(source, folders, files) for source, folders, files in inventories]
    folder_rows = []
    file_rows = []
    summary_rows = []
    source_rows = []
    for source, folders, files in sources:
        profile = get_profile(source)
        counts = Counter(item["folder_id"] for item in files)
        subfolders = Counter(item["parent_id"] for item in folders)
        source_rows.append((source.nome, source.pasta_id, len(folders), len(files), f"https://drive.google.com/drive/folders/{source.pasta_id}",
                            profile.config["origin"] if profile else "", "; ".join(profile.config["related_companies"]) if profile else ""))
        for folder in sorted(folders, key=lambda item: item["path"].casefold()):
            folder_rows.append((source.nome, folder["depth"], folder["path"], folder["name"],
                                counts[folder["id"]], subfolders[folder["id"]], folder["id"], folder["parent_id"], folder["url"], source.pasta_id))
        for item in sorted(files, key=lambda value: (value["folder_path"].casefold(), value["name"].casefold())):
            classification = item.get("classification", {})
            identity = item.get("project_identity", {})
            file_rows.append((source.nome, item["folder_path"], item["name"], item["mime_type"],
                              item["size"], item["modified_time"], item["id"], item["folder_id"], item["url"],
                              identity.get("name", ""), "; ".join(identity.get("companies", [])), identity.get("confidence", ""),
                              classification.get("categoria"), classification.get("pontuacao"), classification.get("revisao"),
                              classification.get("excluido"), classification.get("motivo"), classification.get("versao_comercial", ""), source.pasta_id,
                              item.get("md5_checksum", ""), item.get("sha256_checksum", ""), json.dumps(item.get("image_metadata", {}), sort_keys=True)))
        summary_rows.append((source.nome, len(folders), len(files), sum(item["size"] or 0 for item in files)))
    summary_rows.append(("TOTAL", sum(row[1] for row in summary_rows), sum(row[2] for row in summary_rows), sum(row[3] for row in summary_rows)))
    add_sheet(book, "Resumo", ["Fonte", "Pastas", "Arquivos", "Bytes conhecidos"], summary_rows, [34, 15, 15, 22])
    add_sheet(book, "Fontes", ["Fonte", "ID da pasta raiz", "Pastas", "Arquivos", "Link", "Origem comercial", "Empresas relacionadas (não atribuição)"], source_rows, [34, 42, 15, 15, 55, 40, 45], 5)
    add_sheet(book, "Pastas", ["Fonte", "Nível", "Caminho completo", "Nome", "Arquivos diretos", "Subpastas diretas", "ID", "ID pai", "Link", "source_id"], folder_rows, [34, 10, 65, 35, 18, 20, 43, 43, 55, 43], 9)
    add_sheet(book, "Arquivos", ["Fonte", "Caminho da pasta", "Arquivo", "Tipo MIME", "Tamanho (bytes)", "Modificado em", "ID", "ID da pasta", "Link",
                              "Empreendimento", "Construtoras", "Confiança da identidade", "Categoria", "Pontuação", "Revisão", "Excluído", "Motivo", "Versão comercial", "source_id", "md5_checksum", "sha256_checksum", "dimensoes_imagem"],
              file_rows, [34, 65, 45, 42, 20, 25, 43, 43, 55, 35, 30, 25, 22, 15, 15, 15, 40, 22, 43, 45, 70, 45], 9)
    return book


def atomic_save(book, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(suffix=".xlsx", dir=path.parent, delete=False) as handle:
            temporary = Path(handle.name)
        book.save(temporary)
        os.replace(temporary, path)
    finally:
        book.close()
        if temporary and temporary.exists():
            temporary.unlink()


def write_inventory(path, inventories):
    atomic_save(inventory_book(inventories), path)
