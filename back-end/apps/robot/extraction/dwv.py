"""DWV commercial cards, including sections and units continued across PDF pages."""
import re
from decimal import Decimal

from apps.robot.profiles import normalize
from .common import DeveloperTableParser

MONEY = re.compile(r"R\$\s*(\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2})")
SECTION = re.compile(r"^(.+?)\s*-\s*(\d+)[°ºo]?\s*ANDAR\s*-\s*(.+)$", re.I)
UNIT = re.compile(r"^(\d{1,5})(?:\s+(Dispon[ií]vel|Reservad[oa]|Vendid[oa]|Indispon[ií]vel))?$", re.I)


class DWVTableParser(DeveloperTableParser):
    version = "dwv-1.0.0"

    def parse(self, pages, context):
        full_text = "\n".join(page.text for page in pages)
        month = re.search(r"\b([A-ZÇ]+)\s+DE\s+(20\d{2})\b", full_text, re.I)
        delivery = re.search(r"Previs[aã]o de entrega:\s*([a-zç]+)\s+(20\d{2})", full_text, re.I)
        registration = re.search(r"INCORPORA[ÇC][ÃA]O\s+([\w.\-]+)", full_text, re.I)
        months = {name: i for i, name in enumerate(
            ("janeiro", "fevereiro", "marco", "abril", "maio", "junho", "julho", "agosto", "setembro", "outubro", "novembro", "dezembro"), 1)}
        facts = {}
        if delivery and normalize(delivery[1]) in months:
            facts["previsao_entrega"] = f"{delivery[2]}-{months[normalize(delivery[1])]:02}"
        if registration:
            facts["registro_incorporacao"] = registration[1]
        data_month = f"{month[2]}-{months[normalize(month[1])]:02}" if month and normalize(month[1]) in months else ""
        section = None
        active = None
        payment = ""
        results = []
        seen = set()

        def finish():
            nonlocal active
            if not active:
                return
            block = "\n".join(active["lines"])
            private = re.search(r"[ÁA]rea privativa\s+([\d.,]+)\s*m", block, re.I)
            total = re.search(r"[ÁA]rea total\s+([\d.,]+)\s*m", block, re.I)
            # The sale price is in the explicit total-area/VALOR line. Payment
            # amounts above the unit never become its price, even if larger.
            price_line = next((line for line in active["lines"] if re.search(r"[ÁA]rea total", line, re.I)), "")
            prices = MONEY.findall(price_line)
            status = next((normalize(line) for line in active["lines"] if normalize(line) in
                           ("disponivel", "reservado", "reservada", "vendido", "vendida", "indisponivel")), "")
            bedrooms = re.search(r"(\d+)\s*Dormit[oó]rio", block, re.I)
            suites = re.search(r"sendo\s*(\d+)\s*Su[ií]te", block, re.I)
            raw = {"unidade": active["number"], "andar": active["floor"], "posicao": active["position"],
                   "valor": prices[-1] if len(prices) == 1 else status if status != "disponivel" else "",
                   "area_informada": private[1] if private else total[1] if total else "",
                   "natureza_area_documento": "privativa" if private else "total" if total else "",
                   "data_tabela": data_month, "situacao_comercial": status,
                   "condicoes_pagamento_linha": active["payment"], "linhas_originais": active["lines"],
                   "tipologia": f"{bedrooms[1]} quartos" + (f", {suites[1]} suítes" if suites else "") if bedrooms else ""}
            unit = self.build(raw, active["page"], active["row"], {**context, "document_facts": facts}, 1.0)
            for field, match in (("area_privativa", private), ("area_total", total)):
                if match:
                    unit.fields[field] = str(Decimal(match[1].replace(",", ".")).quantize(Decimal("0.01")))
            unit.warnings.append("VIGENCIA_NAO_CONFIRMADA")
            if status != "disponivel":
                unit.warnings.append("UNIDADE_NAO_DISPONIVEL" if status else "DISPONIBILIDADE_NAO_CONFIRMADA")
            if not data_month:
                unit.warnings.append("DATA_TABELA_NAO_IDENTIFICADA")
            key = (normalize(unit.fields["empreendimento"]), unit.fields["unidade"])
            if key in seen:
                unit.warnings.append("UNIDADE_DUPLICADA_NO_DOCUMENTO")
            seen.add(key)
            unit.warnings = list(dict.fromkeys(unit.warnings))
            results.append(unit)
            active = None

        for page in pages:
            for row_number, line in enumerate(page.text.splitlines(), 1):
                line = line.strip()
                heading = SECTION.fullmatch(line)
                if heading:
                    finish()
                    section = (heading[2], heading[3]) if normalize(heading[1]) == normalize(context.get("empreendimento", "")) else None
                    payment = ""
                    continue
                if not section:
                    continue
                if len(MONEY.findall(line)) >= 2 and not re.search(r"[ÁA]rea", line, re.I):
                    payment = line
                    continue
                number = UNIT.fullmatch(line)
                if number:
                    finish()
                    active = {"number": number[1], "floor": section[0], "position": section[1],
                              "page": page, "row": row_number, "payment": payment,
                              "lines": [number[2]] if number[2] else []}
                    payment = ""
                elif active:
                    active["lines"].append(line)
        finish()
        return results


class IconTableParser(DWVTableParser):
    version = "icon-dwv-1.0.0"
    commercial_origin = "ICON"
