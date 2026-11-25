"""Document-wide facts, including commercial footers on the last page."""

import re


class DocumentFacts:
    MONTHS = {name: index for index, name in enumerate(
        ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"), 1)}

    @classmethod
    def extract(cls, pages):
        facts, evidence = {}, []
        for page in pages:
            address = re.search(r"Endere[çc]o\s*:\s*(.+?)(?=Previs[aã]o\s+de\s+entrega|Registro\s+de\s+Incorpora|\n|$)", page.text, re.I)
            delivery = re.search(r"Previs[aã]o\s+de\s+entrega\s*:\s*([a-zç]+|\d{1,2})\s*[/\-]\s*(\d{2,4})", page.text, re.I)
            registration = re.search(r"Registro\s+de\s+Incorpora[çc][aã]o\s*:\s*([^\n]+)", page.text, re.I)
            if address:
                facts["endereco"] = address.group(1).strip()
                parts = [part.strip() for part in facts["endereco"].split(",")]
                if len(parts) >= 3:
                    facts["bairro"] = parts[-1]
            if delivery:
                name, year = delivery.groups()
                month = int(name) if name.isdigit() else cls.MONTHS.get(name.lower()[:3])
                year = int(year) + (2000 if len(year) == 2 else 0)
                if month and 1 <= month <= 12:
                    facts["previsao_entrega"] = f"{year:04d}-{month:02d}"
            if registration:
                facts["registro_incorporacao"] = registration.group(1).strip()
            if address or delivery or registration:
                evidence.append({"page": page.number, "method": page.method,
                                 "excerpt": " | ".join(m.group(0) for m in (address, delivery, registration) if m)})
        return facts, evidence
