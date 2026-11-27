"""Leitura offline dos inventários V1/V2, sem banco nem acesso ao Drive."""

from types import SimpleNamespace
import json
from collections import defaultdict

from openpyxl import load_workbook


def read_inventory(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sources = {}
        names = defaultdict(list)
        for row in book["Fontes"].iter_rows(min_row=2, values_only=True):
            if row[1] in sources:
                raise ValueError("IDs de fontes duplicados no inventário.")
            sources[row[1]] = (SimpleNamespace(pk=None, nome=row[0], pasta_id=row[1]), [], [])
            names[row[0]].append(row[1])

        def select_source(name, extra):
            source_id = extra.get("source_id")
            if source_id:
                return sources[source_id]
            if len(names[name]) != 1:
                raise ValueError("Nomes de fontes ambíguos em inventário sem source_id.")
            return sources[names[name][0]]

        folder_headers = [cell.value for cell in next(book["Pastas"].iter_rows())]
        for row in book["Pastas"].iter_rows(min_row=2, values_only=True):
            source, folders, _ = select_source(row[0], dict(zip(folder_headers, row)))
            folders.append({"source_id": source.pasta_id, "source_name": source.nome,
                            "depth": row[1], "path": row[2], "name": row[3], "id": row[6],
                            "parent_id": row[7] or "", "url": row[8], "project_id": row[6]})
        file_headers = [cell.value for cell in next(book["Arquivos"].iter_rows())]
        for row in book["Arquivos"].iter_rows(min_row=2, values_only=True):
            extra = dict(zip(file_headers, row))
            source, _, files = select_source(row[0], extra)
            files.append({"source_id": source.pasta_id, "source_name": source.nome,
                          "folder_path": row[1], "name": row[2], "mime_type": row[3], "size": row[4],
                          "modified_time": row[5] or "", "id": row[6], "folder_id": row[7], "url": row[8],
                          "project_id": row[7], "description": "",
                          "md5_checksum": extra.get("md5_checksum") or "", "sha256_checksum": extra.get("sha256_checksum") or "",
                          "image_metadata": json.loads(extra.get("dimensoes_imagem") or "{}")})
        return list(sources.values())
    finally:
        book.close()


def read_rule_snapshot(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        return {row[0]: json.loads(row[3]) for row in book["Regras"].iter_rows(min_row=2, values_only=True)}
    finally:
        book.close()
