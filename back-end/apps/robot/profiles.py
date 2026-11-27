"""Motor único de classificação contextual de metadados do Drive."""

from copy import deepcopy
from dataclasses import dataclass
import re
import unicodedata

ENGINE_VERSION = "2.0.0"
TABLE_MIMES = ("application/pdf", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
               "application/vnd.ms-excel", "text/csv", "application/csv", "application/vnd.google-apps.spreadsheet")
IMAGE_MIMES = ("image/jpeg", "image/png", "image/webp", "image/heif", "image/heic", "image/tiff",
               "image/vnd.adobe.photoshop", "image/x-photoshop", "application/vnd.adobe.photoshop", "image/avif", "image/bmp")
ORGANIZATIONAL = ("tabela", "tabelas", "tabelas comerciais", "black drx", "avulsos", "imagens", "materiais", "book", "books",
                  "material", "comercial", "material comercial", "fotos", "renders", "plantas", "documentacao",
                  "materiais prioritarios", "lancamentos", "em obra", "pronto pra morar", "avulsos tf")


def project_name(value):
    value = re.sub(r"^\s*(?:c[oó]pia de\s*)+", "", value, flags=re.I)
    value = re.sub(r"\.(?:pdf|xlsx?|csv|jpe?g|png|webp|tiff?|heif|heic|psd|avif)$", "", value, flags=re.I)
    value = re.sub(r"^\s*\d{4}[.-]\d{2}\s*[-–]?\s*", "", value)
    value = re.sub(r"\s*\(\d+\s*(?:und|unidades?)\)\s*", "", value, flags=re.I)
    return re.split(r"\s*[:|]\s*", value)[0].strip()


def normalize(value, *, metadata=False):
    value = str(value or "")
    if not metadata:
        value = project_name(value)
    value = unicodedata.normalize("NFKD", value.casefold())
    value = "".join(c for c in value if not unicodedata.combining(c))
    value = re.sub(r"[^a-z0-9]+", " ", value).strip()
    value = re.sub(r"^(?:copia de\s*)+", "", value)
    return re.sub(r"^\d{1,3}\s+(?=[a-z])", "", value)


def contains(text, term):
    term = normalize(term, metadata=True)
    return bool(term) and f" {term} " in f" {normalize(text, metadata=True)} "


def mixed_folder(name):
    words = set(normalize(name, metadata=True).split())
    return bool(words & {"imagens", "renders", "fotos", "tabela", "tabelas"}) and bool(words & {"plantas", "video", "videos", "book"})


@dataclass(frozen=True)
class Company:
    key: str
    name: str


@dataclass(frozen=True)
class ProjectIdentity:
    key: str
    name: str
    companies: tuple[str, ...]
    confidence: str


@dataclass(frozen=True)
class CategoryRule:
    category: str
    folders: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()
    mime_types: tuple[str, ...] = ()

    def compatible(self, mime):
        allowed = self.mime_types or (TABLE_MIMES if self.category == "tabela_precos" else IMAGE_MIMES)
        return mime in allowed

    def score(self, path, name, mime):
        if not self.compatible(mime):
            return 0
        folder_match = any(contains(path, word) for word in self.folders)
        name_match = any(contains(name, word) for word in self.keywords)
        return (95 if name_match and folder_match else 90 if name_match else 85) if folder_match or name_match else 0


def confidence(score, evidence, rule, reason, threshold=80):
    return {"pontuacao": score, "evidencias": evidence, "regra": rule, "motivo": reason, "revisao": score < threshold}


@dataclass(frozen=True)
class SourceProfile:
    config: dict

    @property
    def depth(self):
        return self.config.get("project_depth", 1)

    def is_organizational(self, name):
        text = normalize(name)
        return text in self.config.get("organizational_names", ORGANIZATIONAL) or contains(text, "black drx")

    def identity(self, name):
        name = self.config.get("project_name") or project_name(name)
        if "mga" in self.config.get("related_companies",[]) and normalize(name) in ("mondo","mondo 2"):
            return ProjectIdentity("mga:mondo","Mondo",("mga",),"alta")
        entries = [entry for entry in self.config.get("canonical_projects", [])
                   if normalize(name) in {normalize(alias) for alias in [entry["name"], *entry.get("aliases", [])]}]
        if len({(entry["key"], tuple(entry.get("companies", []))) for entry in entries}) > 1:
            return ProjectIdentity("", "", (), "conflito")
        if entries:
            entry = entries[0]
            return ProjectIdentity(entry["key"], entry["name"], tuple(entry.get("companies", [])), entry.get("confidence", "revisao"))
        if normalize(name) in {"elevare", "mga elevare"}:
            return ProjectIdentity("mga-tropical:elevare", "Elevare", ("mga", "tropical"), "alta")
        if not name or self.is_organizational(name) or self.config.get("mode") in ("commercial_only", "complementary"):
            return ProjectIdentity("", "", (), "nao_resolvida")
        companies = tuple(self.config.get("responsible_companies", []))
        if self.config.get("mixed"):
            companies = ("mga",) if normalize(name) in ("mondo", "mondo 2") else ()
        namespace = "+".join(companies) or self.config["code"]
        return ProjectIdentity(f"{namespace}:{normalize(name)}", name, companies,
                               self.config.get("confidence", "revisao") if companies else "nao_identificada")

    def classify(self, item):
        name, mime = item["name"], item["mime_type"]
        segments = item.get("path_segments") or [
            {"name": segment, "role": "raiz" if i == 0 else "subpasta"}
            for i, segment in enumerate(item["folder_path"].split("/"))
        ]
        result = {"categoria": None, "pontuacao": 0, "revisao": True, "excluido": False,
                  "motivo": "NO_CATEGORY_EVIDENCE", "regras": [], "evidencias": [], "tags": [],
                  "versao_motor": ENGINE_VERSION, "contexto_original": item["folder_path"],
                  "pasta_candidata": False, "prioridade": len(self.config.get("priority_folders", []))}

        def evidence(rule, keyword, segment):
            result["regras"].append(rule)
            result["evidencias"].append({"regra": rule, "palavra": keyword, "segmento": segment})

        def reject(rule, word, segment):
            evidence(rule, word, segment)
            result.update(excluido=True, revisao=False, motivo=rule)
            result["confianca_categoria"] = confidence(0, result["evidencias"], rule, "Material fora das categorias habilitadas")
            return result

        active = {category: config for category, config in self.config.get("categories", {}).items() if config.get("enabled", True)}
        rules = {category: CategoryRule(category, tuple(config.get("folders", [])), tuple([*config.get("keywords", []), *self.config.get("keyword_aliases", {}).get(category, [])]),
                                       tuple(config.get("mime_types", []))) for category, config in active.items()}
        if not any(rule.compatible(mime) for rule in rules.values()):
            return reject("UNSUPPORTED_MIME", mime, "mime_type")

        review = self.config.get("visual_reviews", {}).get(item.get("id"))
        if mime in IMAGE_MIMES and review and review.get("md5") == item.get("md5_checksum"):
            category = review.get("category")
            if category is None:
                return reject("VISUAL_REVIEW_EXCLUDED", review["reason"], name)
            if category in active:
                evidence("CHECKSUM_BOUND_VISUAL_REVIEW", review["reason"], name)
                result.update(categoria=category, pontuacao=100, revisao=False,
                              motivo="CHECKSUM_BOUND_VISUAL_REVIEW", vistoria_visual=True,
                              requires_conversion=False)
                result["confianca_categoria"] = confidence(100, result["evidencias"], result["motivo"], review["reason"])
                return result

        local_exceptions = self.config.get("exclusion_exceptions", ["sala de video", "sala de podcast"])
        if not any(contains(name, term) for term in local_exceptions):
            exclusions = [*self.config.get("exclude", []), "planta", "book", "descritivo", "institucional"]
            for word in exclusions:
                if contains(name, word):
                    code = "MARKETING_ASSET" if normalize(word) in {"feed", "story", "stories", "reels", "card", "criativos", "instagram"} else "TECHNICAL_DOCUMENT"
                    return reject(code, word, name)
        usable_segments = []
        for segment in segments:
            value, role = segment["name"], segment["role"]
            if role in ("raiz", "arquivo"):
                continue
            if mixed_folder(value):
                evidence("MIXED_FOLDER_ALLOWED", "", value)
                usable_segments.append(value)
                continue
            if role == "empreendimento":
                continue
            for word in self.config.get("exclude", []):
                if contains(value, word):
                    code = "MARKETING_ASSET" if normalize(word) in {"feed", "story", "stories", "reels", "card", "criativos", "instagram", "divulgacao"} else "TECHNICAL_DOCUMENT"
                    return reject(code, word, value)
            usable_segments.append(value)

        matches = []
        for category, rule in rules.items():
            if not rule.compatible(mime):
                continue
            file_terms = [word for word in rule.keywords if contains(name, word)]
            folder_terms = [(word, value) for value in usable_segments for word in rule.folders if contains(value, word)]
            joined = "/".join(usable_segments)
            folder_terms += [(word, joined) for word in rule.folders if "/" in word and contains(joined, word)]
            if file_terms or folder_terms:
                score = 95 if file_terms and folder_terms else 90 if file_terms else 85
                matches.append((score, category, file_terms, folder_terms))

        semantics = [(phrase, category) for phrase, category in self.config.get("semantic_phrases", {}).items()
                     if category in rules and rules[category].compatible(mime) and contains(name, phrase)]
        if semantics:
            longest = max(len(normalize(phrase).split()) for phrase, _ in semantics)
            specific = [(phrase, category) for phrase, category in semantics if len(normalize(phrase).split()) == longest]
            if len({category for _, category in specific}) == 1:
                matches = [(98, specific[0][1], [phrase for phrase, _ in specific], [])]
                evidence("SPECIFIC_EXPRESSION_MATCH", specific[0][0], name)
                result["tags"].extend([normalize(phrase) for phrase, _ in specific])

        matches.sort(key=lambda match: (-match[0], match[1]))
        if matches:
            score, category, file_terms, folder_terms = matches[0]
            ambiguous = len(matches) > 1 and matches[1][0] == score
            for word in file_terms:
                evidence("FILENAME_KEYWORD_MATCH", word, name)
            for word, value in folder_terms:
                evidence("CATEGORY_FOLDER_MATCH", word, value)
            result.update(categoria=None if ambiguous else category, pontuacao=score,
                          motivo="AMBIGUOUS_CATEGORY" if ambiguous else "COMMERCIAL_TABLE_MATCH" if category == "tabela_precos" else result["regras"][-1])
            if ambiguous:
                result["categorias_candidatas"] = [match[1] for match in matches if match[0] == score]
                evidence("AMBIGUOUS_CATEGORY", "", name)
        elif mime in TABLE_MIMES:
            result["motivo"] = "AMBIGUOUS_COMMERCIAL_DOCUMENT"

        if result["categoria"] == "tabela_precos":
            evidence("COMMERCIAL_TABLE_MATCH", "tabela candidata, conteúdo não validado", name)
            text = f"{item['folder_path']}/{name}"
            result["versao_comercial"] = "promocional" if any(contains(text, word) for word in ("black drx", "promocional")) else "convencional"
            result["vigencia"] = "nao_confirmada"
            result["validar_atualidade"] = True
        result["pasta_candidata"] = any(contains(value, word) for value in usable_segments for word in self.config.get("candidate_folders", []))
        for i, word in enumerate(self.config.get("priority_folders", [])):
            if any(contains(value, word) for value in usable_segments):
                result["prioridade"] = i
                break
        threshold = self.config.get("thresholds", {}).get("category", 80)
        result["confianca_categoria"] = confidence(result["pontuacao"], result["evidencias"], result["motivo"],
                                                       "Correspondência contextual de metadados; não é validação de conteúdo", threshold)
        result["revisao"] = not result["categoria"] or result["pontuacao"] < threshold or self.config.get("mode") in ("complementary", "commercial_only", "avulsos")
        result["requires_conversion"] = mime in ("image/heif", "image/heic", "image/tiff", "image/vnd.adobe.photoshop", "image/x-photoshop", "application/vnd.adobe.photoshop")
        return result


def get_profile(source):
    from .profile_defaults import DEFAULT_PROFILES, upgrade_profile

    config = getattr(source, "perfil", None) or DEFAULT_PROFILES.get(source.pasta_id)
    return SourceProfile(upgrade_profile(deepcopy(config))) if config else None
