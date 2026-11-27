"""SETAI price grids: retain unit numbers, total areas and dated price evidence."""

import re

from apps.robot.profiles import normalize
from .common import DeveloperTableParser, decimal_br, text


class SetaiTableParser(DeveloperTableParser):
    version = "setai-1.0.0"
    commercial_origin = "Grupo Pirâmide"

    def parse(self, pages, context):
        results = []
        seen = set()
        for page in pages:
            for table in page.tables:
                columns = {}
                area_kind = ""
                price_date = ""
                for row_number, cells in enumerate(table, 1):
                    labels = [normalize(text(cell), metadata=True) for cell in cells]
                    if "unidade" in labels and "valor" in labels:
                        columns = {"unidade": labels.index("unidade"), "valor": labels.index("valor")}
                        area_columns = [i for i, label in enumerate(labels) if label.startswith("area")]
                        if area_columns:
                            columns["area_informada"] = area_columns[0]
                        if "posicao" in labels:
                            columns["posicao"] = labels.index("posicao")
                        continue
                    if not columns:
                        continue
                    joined = " ".join(labels)
                    if "area total" in joined:
                        area_kind = "total"
                    elif "area privativa" in joined:
                        area_kind = "privativa"
                    if not text(cells[columns["unidade"]]):
                        match = re.search(r"\b\d{2}/\d{2}/\d{4}\b", " ".join(text(c) for c in cells))
                        if match:
                            price_date = match.group()
                        continue
                    raw = {key: text(cells[index]) for key, index in columns.items() if index < len(cells)}
                    if not re.fullmatch(r"\d+[A-Za-z]?", raw.get("unidade", "")):
                        continue
                    raw.update(condicoes_originais=cells, natureza_area_documento=area_kind,
                               data_tabela=price_date, origem_comercial="Grupo Pirâmide")
                    unit = self.build(raw, page, row_number, context, 1.0)
                    # A dated table proves its own prices, not current availability.
                    unit.warnings.extend(["VIGENCIA_NAO_CONFIRMADA", "DISPONIBILIDADE_NAO_CONFIRMADA"])
                    if not price_date:
                        unit.warnings.append("DATA_TABELA_NAO_IDENTIFICADA")
                    if not area_kind:
                        unit.warnings.append("NATUREZA_AREA_NAO_CONFIRMADA")
                    if decimal_br(raw.get("valor")) is None:
                        unit.warnings.append("PRECO_NAO_IDENTIFICADO")
                    key = (normalize(unit.fields["empreendimento"]), unit.fields["torre"], unit.fields["unidade"])
                    if key in seen:
                        unit.warnings.append("UNIDADE_DUPLICADA_NO_DOCUMENTO")
                    seen.add(key)
                    results.append(unit)
        return results
