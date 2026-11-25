"""Padrões MGA: avulsos e tabelas de unidades, com total separado das parcelas."""

from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
import re
from statistics import median

from apps.robot.profiles import normalize
from .document_facts import DocumentFacts
from .defaults import CommercialDefaults
from apps.locations.addressing import AddressNormalizer


HEADER_ALIASES = {
    "empreendimento": ("empreendimento",), "unidade": ("unidade", "unid", "apartamento", "apto", "loja"),
    "medidas": ("medidas",), "area_informada": ("area", "area m", "area m2", "area privativa", "area total"),
    "valor": ("valor total", "valor", "preco", "preco total", "locacao mensal"), "endereco": ("endereco",),
    "descricao": ("descricao",), "tipologia": ("tipologia",), "posicao": ("posicao",),
    "vagas": ("vagas", "garagens"), "torre": ("torre", "bloco"), "andar": ("andar",),
}


def text(value):
    return " ".join(str(value or "").split())


def decimal_br(value):
    compact = re.sub(r"\s+", "", str(value or "")).replace("R$", "")
    compact = re.sub(r"^RS", "", compact, flags=re.I)
    if not compact:
        return None
    if not re.fullmatch(r"\d{1,3}(?:\.\d{3})*,\d{2}|\d+,\d{2}|\d+(?:\.\d{1,2})?", compact):
        return None
    if "," in compact:
        compact = compact.replace(".", "").replace(",", ".")
    try:
        result = Decimal(compact)
        return str(result.quantize(Decimal("0.01"))) if result > 0 else None
    except InvalidOperation:
        return None


@dataclass
class ExtractedUnit:
    fields: dict
    raw: dict
    page: int
    row: int
    method: str
    warnings: list = field(default_factory=list)
    confidence: float = 1.0

    def as_dict(self):
        return asdict(self)


class DeveloperTableParser(ABC):
    @abstractmethod
    def parse(self, pages, context):
        raise NotImplementedError


class MGATableParser(DeveloperTableParser):
    version = "mga-1.6.0"

    def header(self, cells):
        mapping = {}
        for index, cell in enumerate(cells):
            first = str(cell or "").split("\n")[0]
            normalized = normalize(first)
            for key, aliases in HEADER_ALIASES.items():
                if normalized in aliases:
                    mapping[index] = key
                    break
        # PDF grids may merge several header cells while preserving separate
        # data columns. Recover their spans before falling back to coordinates;
        # otherwise a boundary between R$ / 2 / .122.036,00 truncates the price.
        aliases = sorted(((alias, key) for key, values in HEADER_ALIASES.items() for alias in values),
                         key=lambda item: len(item[0]), reverse=True)
        pattern = r"(?<!\w)(?:" + "|".join(re.escape(alias) for alias, _ in aliases) + r")(?!\w)"
        keys = dict(aliases)
        for index, cell in enumerate(cells):
            first = normalize(str(cell or "").split("\n")[0])
            matches = list(re.finditer(pattern, first))
            end = next((i for i in range(index + 1, len(cells)) if cells[i] is not None), len(cells))
            if len(matches) > 1 and len(matches) <= end - index:
                for offset, match in enumerate(matches):
                    mapping[index + offset] = keys[match.group()]
        return mapping if "unidade" in mapping.values() and "valor" in mapping.values() else {}

    def table_rows(self, table):
        mapping = {}
        other_headers = {}
        last_floor = ""
        area_kind = ""

        def with_floor(values):
            nonlocal last_floor
            if "andar" not in values:
                return values
            original = values["andar"]
            parts = original.split()
            if parts and len(set(parts)) == 1 and parts[0].isdigit():
                values["andar"] = parts[0]
                last_floor = parts[0]
            elif not original and last_floor:
                values["andar"] = last_floor
            if values["andar"] != original:
                values["andar_original"] = original
                values["andar_origem"] = "celula_mesclada_da_grade"
            return values

        def with_metadata(values):
            if area_kind:
                values["natureza_area_documento"] = area_kind
            return with_floor(values)
        for index, cells in enumerate(table):
            header = self.header(cells)
            if header:
                mapping = header
                area_kind = next(("total" if normalize(str(cells[column]),metadata=True)=="area total" else "privativa"
                                  for column,key in mapping.items() if key=="area_informada" and
                                  normalize(str(cells[column]),metadata=True) in ("area total","area privativa")), "")
                other_headers = {column: str(cell or "").split("\n")[0].strip() for column, cell in enumerate(cells)
                                 if column not in mapping and str(cell or "").split("\n")[0].strip()}
                # Algumas grades unem o cabeçalho e a primeira unidade.
                remainder = ["\n".join(str(cell or "").split("\n")[1:]) for cell in cells]
                values = {key: text(remainder[column]) for column, key in mapping.items()}
                if values.get("unidade"):
                    yield index + 1, with_metadata(values), 1.0
                continue
            if mapping:
                values = {key: text(cells[column]) for column, key in mapping.items() if column < len(cells)}
                if values.get("unidade"):
                    # Condições de pagamento continuam auditáveis, sem confundir
                    # sinal/mensais com valor total do imóvel.
                    values["condicoes_originais"] = list(cells)
                    values["condicoes_pagamento"] = {label: text(cells[column]) for column, label in other_headers.items() if column < len(cells)}
                    yield index + 1, with_metadata(values), 1.0

    def word_rows(self, page):
        words = page.words
        if not words:
            return
        tolerance = max(3, median(word["bottom"] - word["top"] for word in words) * .55)
        lines = []
        for word in sorted(words, key=lambda word: ((word["top"] + word["bottom"]) / 2, word["x0"])):
            center = (word["top"] + word["bottom"]) / 2
            if not lines or center - lines[-1][0] > tolerance:
                lines.append([center, []])
            lines[-1][1].append(word)
        header_line = None
        for y, line in lines:
            line = sorted(line, key=lambda word: word["x0"])
            mapping = self.header([word["text"] for word in line])
            if mapping and len(mapping) >= 3:
                header_line = y, line, mapping
                break
        if header_line is None:
            return
        y, line, mapping = header_line
        # Inclui também cabeçalhos de pagamento, para limitar a coluna de valor.
        centers = [(word["x0"] + word["x1"]) / 2 for word in line]
        boundaries = [0, *[(left + right) / 2 for left, right in zip(centers, centers[1:])], page.width]
        unit_col = next(column for column, key in mapping.items() if key == "unidade")
        anchors = []
        for word in words:
            x, wy = (word["x0"] + word["x1"]) / 2, (word["top"] + word["bottom"]) / 2
            if wy <= y + tolerance or not boundaries[unit_col] <= x < boundaries[unit_col + 1]:
                continue
            if re.fullmatch(r"\d{1,5}[A-Za-z]?", text(word["text"])) or re.match(r"(?i)^(quadra|t[eé]rreo|loja|sala|lote)", text(word["text"])):
                if anchors and wy - anchors[-1] < tolerance * 2.5:
                    continue
                anchors.append(wy)
        anchors.sort()
        row_bounds = [y + tolerance, *[(a + b) / 2 for a, b in zip(anchors, anchors[1:])], page.height]
        for index in range(len(anchors)):
            cells = {key: [] for key in mapping.values()}
            scores = []
            for word in words:
                x, wy = (word["x0"] + word["x1"]) / 2, (word["top"] + word["bottom"]) / 2
                if row_bounds[index] <= wy < row_bounds[index + 1]:
                    for column, key in mapping.items():
                        if boundaries[column] <= x < boundaries[column + 1]:
                            cells[key].append(word)
                            scores.append(word.get("score", 0))
            yield index + 1, {key: text(" ".join(word["text"] for word in sorted(values, key=lambda word: (word["top"], word["x0"])))) for key, values in cells.items()}, min(scores, default=0)

    def build(self, raw, page, row, context, score):
        name = raw.get("empreendimento") or context.get("empreendimento", "")
        unit = raw.get("unidade", "")
        if normalize(unit) in ("unidade", "total", "obs") or len(unit) > 80:
            return None
        page_text = normalize(page.text, metadata=True)
        rental = "locacao mensal" in page_text or "lojas mondo locacao" in page_text
        data = {"empreendimento": name, "unidade": unit, "torre": raw.get("torre", ""), "andar": raw.get("andar", ""), "tipologia": raw.get("tipologia", ""), "medidas": raw.get("medidas", ""),
                "area_informada": decimal_br(raw.get("area_informada")), "valor": decimal_br(raw.get("valor")),
                "endereco": raw.get("endereco", ""), "descricao": raw.get("descricao", ""),
                "tipo": "", "cidade": "", "bairro": "", "uf": "PB", "finalidade": "aluguel" if rental else "venda" if "vendas" in page_text else context.get("document_purpose", ""),
                "origem_comercial": "MGA Construções", "construtora": context.get("construtora", "")}
        description = normalize(data["descricao"] + " " + unit + " " + raw.get("tipologia", ""), metadata=True)
        if re.search(r"\b(loja|lojas|sala comercial)\b", description) or rental or normalize(raw.get("tipologia", ""), metadata=True) == "sala":
            data["tipo"] = "comercial"
        elif "cobertura" in description:
            data["tipo"] = "cobertura"
        elif re.search(r"\b(lote|quadra|terreno)\b", description):
            data["tipo"] = "terreno"
        elif re.search(r"\bapartamento\b|\d+\s*(?:quartos?|qts|suites?)\b", description):
            data["tipo"] = "apartamento"
        elif "studio" in description or "flat" in description:
            data["tipo"] = "flat"
        elif re.fullmatch(r"\d+",unit) and "apartamentos mondo" in page_text:
            data["tipo"] = "apartamento"
            raw["tipo_origem"] = "cabecalho_apartamentos_mondo"
        if not data["endereco"]:
            for line in page.text.splitlines():
                if re.match(r"\s*(?:R\.|Rua |Av\.|Avenida |Rodovia )", line, re.I):
                    data["endereco"] = re.split(r"Registro de incorpora|Previs[aã]o de Entrega", line, flags=re.I)[0].strip()
                    break
        if not data["endereco"] and context.get("document_facts", {}).get("endereco"):
            data["endereco"] = context["document_facts"]["endereco"]
        address = normalize(data["endereco"], metadata=True)
        for normalized, city in (("joao pessoa", "João Pessoa"), ("bananeiras", "Bananeiras"), ("cabedelo", "Cabedelo")):
            if normalized in address:
                data["cidade"] = city
        district = re.search(r"\s[-–]\s*([^,]+),\s*(?:Jo[aã]o Pessoa|Cabedelo|Bananeiras)", data["endereco"], re.I)
        if district:
            data["bairro"] = district.group(1).strip()
        for field_name, pattern in (("quartos", r"(\d+)\s*(?:quartos?|qts)"), ("suites", r"(\d+)\s*su[ií]tes?"), ("vagas", r"(\d+)\s*vagas?")):
            found = re.search(pattern, data["descricao"] + " " + raw.get("tipologia", ""), re.I)
            if found:
                data[field_name] = int(found.group(1))
        if raw.get("vagas", "").isdigit():
            data["vagas"] = int(raw["vagas"])
        if data.get("suites"):
            data["quartos"] = max(data.get("quartos", 0), data["suites"])
        for key, value in context.get("document_facts", {}).items():
            if not data.get(key):
                data[key] = value
        if context.get("document_evidence"):
            raw["documento"] = context["document_evidence"]
        area_kind=context.get("natureza_area") or raw.get("natureza_area_documento")
        if area_kind and data["area_informada"]:
            data["area_total" if area_kind == "total" else "area_privativa"] = data["area_informada"]
            raw["natureza_area_contexto"] = area_kind
        if "mobiliada" in description or "mobiliado" in description:
            data["mobiliado"] = True
        # Contexto fornecido pelo operador é explícito e permanece na auditoria.
        for key in ("cidade", "bairro", "tipo", "finalidade", "construtora", "endereco"):
            if context.get(key):
                data[key] = context[key]
        data, decisions = CommercialDefaults.apply(data, avulso=context.get("avulso", False))
        if decisions:
            raw["regras_padrao"] = decisions
        if data["cidade"] == "Bananeiras":
            data["bairro"] = "Centro"
        warnings = [f"CAMPO_PENDENTE:{key}" for key in ("empreendimento", "unidade", "valor", "tipo", "finalidade", "cidade", "bairro") if not data.get(key)]
        if rental and context.get("finalidade") == "venda":
            warnings.append("CONFLITO_FINALIDADE")
        if data["tipo"] == "comercial" and ("studio" in description or "quarto" in description):
            warnings.append("CONFLITO_TIPOLOGIA")
        if page.method == "ocr":
            warnings.append("OCR_REQUER_CONFERENCIA")
        if any(term in normalize(raw.get("valor", "")) for term in ("vendido", "reservado", "indisponivel")):
            warnings.append("UNIDADE_NAO_DISPONIVEL")
        if score < .95:
            warnings.append("BAIXA_CONFIANCA_OCR")
        if data["valor"] and data["finalidade"] != "aluguel" and Decimal(data["valor"]) < 1000:
            warnings.append("PRECO_SUSPEITO")
        return ExtractedUnit(data, raw, page.number, row, page.method, warnings, score)

    def parse(self, pages, context):
        context = dict(context)
        from apps.robot.project_context import canonical_project, verified_context
        if context.get("empreendimento"):
            context["empreendimento"] = canonical_project(context["empreendimento"])
            context.update(verified_context(context["empreendimento"]))
        if not context.get("empreendimento") and any("empreendimento" in self.header(row).values() for page in pages for table in page.tables for row in table):
            context["avulso"] = True
        # Operator-approved interpretation of this project's generic area column.
        if normalize(context.get("empreendimento", "")) == "elevare":
            context.setdefault("natureza_area", "total")
        # A catalog of unrelated avulsos cannot inherit one property's footer.
        if context.get("empreendimento") and not any("empreendimento" in self.header(row).values() for page in pages for table in page.tables for row in table):
            context["document_facts"], context["document_evidence"] = DocumentFacts.extract(pages)
        if any("vendas" in normalize(page.text, metadata=True) for page in pages):
            context["document_purpose"] = "venda"
        elif any("sinal" in normalize(page.text, metadata=True) and
                 ("parcela final" in normalize(page.text, metadata=True) or "parcelas" in normalize(page.text, metadata=True)) for page in pages):
            context["document_purpose"] = "venda"
        elif context.get("empreendimento") == "Mondo" and any("valor total" in normalize(page.text,metadata=True) for page in pages):
            # Mondo's total sale-price sections are distinct from its explicit
            # "Locação Mensal" section, which takes precedence per page.
            context["document_purpose"] = "venda"
        results = []
        seen = set()
        for page in pages:
            table_rows = [(row, values, score) for table in page.tables for row, values, score in self.table_rows(table)]
            for row, raw, score in table_rows or list(self.word_rows(page)):
                candidate = self.build(raw, page, row, context, score)
                if candidate is None:
                    continue
                key = (normalize(candidate.fields["empreendimento"]), normalize(candidate.fields["unidade"]), normalize(candidate.fields["torre"]))
                if key in seen:
                    candidate.warnings.append("UNIDADE_DUPLICADA_NO_DOCUMENTO")
                seen.add(key)
                results.append(candidate)
        return results
