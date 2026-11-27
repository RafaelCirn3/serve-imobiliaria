"""Local address parsing and ordered neighborhood recognition, without I/O."""

import re

from .normalization import canonical_city, normalized

# Names confirmed in the municipal neighborhood map and present in our sources.
JOAO_PESSOA_DISTRICTS = ("Altiplano", "Cabo Branco", "Jardim Oceania", "Tambaú", "Brisamar", "Bessa")


class AddressNormalizer:
    @staticmethod
    def district(value, city=""):
        if city and canonical_city(city) != "João Pessoa":
            return None
        matches = []
        for district in JOAO_PESSOA_DISTRICTS:
            pattern = r"\s*".join(re.escape(part) for part in normalized(district).split())
            match = re.search(r"(?<!\w)" + pattern + r"(?!\w)", normalized(value))
            if match:
                matches.append((match.start(), district))
        return min(matches)[1] if matches else None

    @classmethod
    def parse(cls, data):
        result = {key: data.get(key, "") or "" for key in
                  ("endereco", "logradouro", "numero", "complemento", "cidade", "bairro", "uf", "cep")}
        raw = re.sub(r"^\s*Endere[çc]o\s*:\s*", "", result["endereco"], flags=re.I).strip()
        parts = [part.strip() for part in raw.split(",")]
        first = parts[0] if parts else ""
        street_and_district = re.split(r"\s+[-–]\s+", first, maxsplit=1)
        if not result["logradouro"] and re.match(r"^(?:Rua\s+|R\.\s*|Av\.\s*|Av\s+|Avenida\s+|Rodovia\s+)", first, re.I):
            result["logradouro"] = re.sub(r"^Av\.\s*", "Avenida ", re.sub(r"^R\.\s*", "Rua ", street_and_district[0], flags=re.I), flags=re.I)
        tail = " ".join(parts[1:])
        if len(street_and_district) > 1:
            tail = street_and_district[1] + " " + tail
        if len(parts) > 1:
            number = re.match(r"^(\d+[A-Za-z]?|s/n)(?=\b|\s|$)", parts[1], re.I)
            if number and not result["numero"]:
                result["numero"] = number.group(1)
        if not result["cidade"]:
            result["cidade"] = next((city for city in ("João Pessoa", "Cabedelo", "Bananeiras")
                                     if re.search(r"\s*".join(map(re.escape, normalized(city).split())), normalized(tail))), "")
        district = cls.district(result["bairro"] or tail, result["cidade"])
        if district:
            result["bairro"], result["cidade"] = district, "João Pessoa"
        result["cidade"] = canonical_city(result["cidade"]) or result["cidade"]
        if result["cidade"] == "Bananeiras":
            # Business catalog rule supplied by the operator; retain the raw
            # locality in endereco and postal evidence, not in the main bairro.
            result["bairro"] = "Centro"
        if result["cidade"]:
            result["uf"] = result["uf"] or "PB"
        return result

    @staticmethod
    def street_key(value):
        value = re.sub(r"^(?:rua|r\.|avenida|av\.?|rodovia)\s+", "", normalized(value), flags=re.I)
        return " ".join(value.split())
