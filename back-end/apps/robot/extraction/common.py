"""Shared types, numeric normalization and unit construction for developer adapters."""
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from decimal import Decimal, InvalidOperation
import re
from apps.robot.profiles import normalize
from .defaults import CommercialDefaults


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
    commercial_origin = ""
    numeric_apartment_evidence = "cabecalho_apartamentos"

    def is_rental_page(self, page_text):
        return "locacao mensal" in page_text

    def is_numeric_apartment_page(self, page_text):
        return False

    @abstractmethod
    def parse(self, pages, context):
        raise NotImplementedError


    def build(self, raw, page, row, context, score):
        name = raw.get("empreendimento") or context.get("empreendimento", "")
        unit = raw.get("unidade", "")
        if normalize(unit) in ("unidade", "total", "obs") or len(unit) > 80:
            return None
        page_text = normalize(page.text, metadata=True)
        rental = self.is_rental_page(page_text)
        data = {"empreendimento": name, "unidade": unit, "torre": raw.get("torre", ""), "andar": raw.get("andar", ""), "tipologia": raw.get("tipologia", ""), "medidas": raw.get("medidas", ""),
                "area_informada": decimal_br(raw.get("area_informada")), "valor": decimal_br(raw.get("valor")),
                "endereco": raw.get("endereco", ""), "descricao": raw.get("descricao", ""),
                "tipo": "", "cidade": "", "bairro": "", "uf": "PB", "finalidade": "aluguel" if rental else "venda" if "vendas" in page_text else context.get("document_purpose", ""),
                "origem_comercial": self.commercial_origin, "construtora": context.get("construtora", "")}
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
        elif re.fullmatch(r"\d+",unit) and self.is_numeric_apartment_page(page_text):
            data["tipo"] = "apartamento"
            raw["tipo_origem"] = self.numeric_apartment_evidence
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

