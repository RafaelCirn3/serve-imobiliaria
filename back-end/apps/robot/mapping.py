"""Agrupamento contextual e decisões comuns ao Drive e ao replay offline."""

from collections import defaultdict
import re

from .profiles import ENGINE_VERSION, IMAGE_MIMES, TABLE_MIMES, confidence, contains, get_profile, mixed_folder, normalize, project_name


def clean_project(value, code):
    value = project_name(value)
    if code in ("02", "10"):
        value = re.split(r"\s+-\s*|(?<=\d)-\s+", value)[0].strip()
    return value


def filename_project(name, code):
    value = project_name(name)
    value = re.sub(r"^\s*\d+[. -]+", "", value)
    value = re.sub(r"^tabela(?:s)?\s+(?:de\s+(?:pre[cç]os?|vendas?)\s+(?:do\s+)?)?", "", value, flags=re.I)
    value = re.sub(r"[_\s-]+(?:\d{2}[_ .-]+\d{4}|\d{4}[.-]\d{2})\s*$", "", value)
    value = value.replace("_", " ").strip(" -")
    if code == "BASE-01":
        value = re.sub(r"^ALLIANCE\s+", "", value, flags=re.I)
    return re.sub(r"\s+", " ", value).strip()


def annotate_inventory(source, folders, files):
    profile = get_profile(source)
    if not profile:
        return folders, files
    config, code = profile.config, profile.config["code"]
    by_id = {folder["id"]: folder for folder in folders}

    def chain(folder_id):
        result, seen = [], set()
        while folder_id in by_id and folder_id not in seen:
            seen.add(folder_id)
            result.append(by_id[folder_id])
            folder_id = by_id[folder_id]["parent_id"]
        return list(reversed(result))

    def is_project(folder):
        name = clean_project(folder["name"], code)
        if folder["depth"] == 0 or profile.is_organizational(name):
            return False
        if normalize(name) in {"books", "documentacoes", "cards de vendas", "tabela avulsos"}:
            return False
        if not mixed_folder(folder["name"]) and any(contains(folder["name"], term) for term in config.get("exclude", [])):
            return False
        return folder["depth"] >= profile.depth

    for folder in folders:
        folder["structural_role"] = "raiz" if folder["depth"] == 0 else "organizacional" if profile.is_organizational(folder["name"]) else "mista" if mixed_folder(folder["name"]) else "subpasta"
        folder["grouping_rule"] = f"PROFILE_DEPTH_{profile.depth}"

    for item in files:
        ancestry = chain(item["folder_id"])
        project_folder = None
        project_text, rule = "", "UNKNOWN_PROJECT"
        if config.get("project_name"):
            project_text = config["project_name"]
            project_folder = ancestry[0] if ancestry else None
            rule = "SINGLE_PROJECT_PROFILE"
        elif config.get("mode") not in ("complementary", "commercial_only"):
            candidates = [folder for folder in ancestry if is_project(folder)]
            if candidates:
                project_folder = candidates[0]
                project_text = clean_project(project_folder["name"], code)
                rule = "PROJECT_FOLDER_MATCH"

        central = config.get("central_tables") and item["mime_type"] in TABLE_MIMES and (
            not project_text or profile.is_organizational(project_text))
        if central:
            text = filename_project(item["name"], code)
            # Só derivar identidade de nomes comerciais em fontes explicitamente
            # configuradas para tabelas centralizadas; book/descritivo não é nome.
            if text and not any(contains(text, word) for word in ("book", "descritivo", "tabela", "imoveis", "terreno")):
                aliases = config.get("project_aliases", {})
                project_text = aliases.get(normalize(text), text.title())
                exact = [folder for folder in folders if normalize(clean_project(folder["name"], code)) == normalize(project_text)]
                if len(exact) == 1:
                    project_folder = exact[0]
                rule = "CENTRAL_TABLE_FILENAME"

        aliases = config.get("project_aliases", {})
        project_text = aliases.get(normalize(project_text), project_text)
        identity = profile.identity(project_text)
        segments = []
        for folder in ancestry:
            role = folder["structural_role"]
            if folder is project_folder and folder["depth"] > 0:
                role = "empreendimento"
                folder["structural_role"] = role
                folder["project_name"] = identity.name
            elif folder["depth"] > 0 and role == "subpasta":
                if any(contains(folder["name"], term) for category in config["categories"].values() for term in category.get("folders", [])):
                    role = "categoria"
            segments.append({"name": folder["name"], "id": folder["id"], "role": role})
        item["path_segments"] = [*segments, {"name": item["name"], "id": item["id"], "role": "arquivo"}]
        item["project_id"] = project_folder["id"] if project_folder else item["folder_id"]
        thresholds = config.get("thresholds", {})
        project_score = 95 if identity.name and rule != "UNKNOWN_PROJECT" else 0
        developer_score = (90 if identity.confidence == "alta" else 50) if identity.companies else 0
        if config.get("mode") == "avulsos" or any(contains(segment["name"], "avulsos") for segment in segments[1:]):
            developer_score = 0
        item["project_identity"] = {
            "key": identity.key, "name": identity.name, "original": project_folder["name"] if project_folder else "",
            "companies": list(identity.companies) if developer_score else [], "related_companies": config.get("related_companies", []),
            "confidence": identity.confidence if developer_score else "nao_identificada", "rule": rule,
            "aliases": [entry.get("aliases", []) for entry in config.get("canonical_projects", []) if entry["key"] == identity.key],
            "project_confidence": confidence(project_score, [project_text] if project_text else [], rule, "Nome exato de pasta, perfil ou tabela centralizada", thresholds.get("project", 80)),
            "developer_confidence": confidence(developer_score, list(identity.companies), "PROFILE_COMPANY" if developer_score else "UNKNOWN_DEVELOPER", "Atribuição do perfil ou alias explícito; origem comercial não comprova responsabilidade", thresholds.get("developer", 80)),
        }
        roles = config.get("company_roles", {})
        item["project_identity"]["developers"] = [company for company in identity.companies if developer_score and roles.get(company, "construtora") == "construtora"]
        item["project_identity"]["incorporators"] = [company for company in identity.companies if developer_score and roles.get(company) == "incorporadora"]
        item["unit_context"] = [segment["name"] for segment in segments if any(contains(segment["name"], term) for term in ("torre", "bloco", "lojas", "loja", "sala", "apto", "aptos", "apartamento", "final", "unidade"))]
        classification = profile.classify(item)
        historical = next((term for term in config.get("historical_terms", ("100% vendido", "vendido", "esgotado", "indisponivel", "tabela antiga", "arquivo historico")) if contains(item["folder_path"] + "/" + item["name"], term)), None)
        classification["situacao_comercial"] = "historico_ou_indisponivel" if historical else "nao_confirmada"
        classification["elegivel_anuncio"] = False  # Conteúdo e disponibilidade ainda não homologados.
        if historical:
            classification["tags"].append("historico")
            classification["regras"].append("SOLD_PROJECT")
            classification["evidencias"].append({"regra": "SOLD_PROJECT", "palavra": historical, "segmento": item["folder_path"]})
            if classification.get("categoria") == "tabela_precos":
                classification["versao_comercial"] = "historica"
        reasons = []
        if identity.confidence == "conflito":
            reasons.append("IDENTITY_CONFLICT")
        if not classification["categoria"]:
            reasons.append(classification["motivo"] if item["mime_type"] not in IMAGE_MIMES else "VISUAL_CLASSIFICATION_REQUIRED" if classification["motivo"] != "AMBIGUOUS_CATEGORY" else "AMBIGUOUS_CATEGORY")
        if item["project_identity"]["project_confidence"]["revisao"]:
            reasons.append("UNKNOWN_PROJECT")
        if item["project_identity"]["developer_confidence"]["revisao"]:
            reasons.append("UNKNOWN_DEVELOPER")
        if classification.get("validar_atualidade"):
            reasons.append("COMMERCIAL_VALIDATION_REQUIRED")
        if historical:
            reasons.append("SOLD_PROJECT")
        if classification["revisao"] and not reasons:
            reasons.append("CATEGORY_OR_SOURCE_REVIEW")
        classification["motivos_revisao"] = reasons if not classification["excluido"] else []
        classification["revisao"] = bool(classification["motivos_revisao"])
        classification["status_decisao"] = "DESCARTADO" if classification["excluido"] else "REVISAO" if classification["revisao"] else "SELECIONADO"
        classification["candidato_selecionado"] = bool(classification["categoria"] and not classification["excluido"])
        item["classification"] = classification
    return folders, files


def audit_duplicates(inventories):
    """IDs/checksums confirmam; nome+tamanho são apenas suspeitas."""
    indexes = {"DRIVE_ID": defaultdict(list), "CHECKSUM": defaultdict(list), "NAME_SIZE": defaultdict(list)}
    items = {}
    for source, _, files in inventories:
        for item in files:
            ref = (source.pasta_id, item["id"], item["name"])
            items[ref[:2]] = item
            indexes["DRIVE_ID"][item["id"]].append(ref)
            checksum = item.get("sha256_checksum") or item.get("md5_checksum")
            if checksum:
                indexes["CHECKSUM"][(checksum, item.get("size"))].append(ref)
            if item.get("size") is not None:
                indexes["NAME_SIZE"][(normalize(item["name"]), item["size"])].append(ref)
    rows = []
    for kind, index in indexes.items():
        for key, references in sorted(index.items(), key=lambda pair: str(pair[0])):
            if len(references) > 1:
                def publication_rank(reference):
                    item = items[reference[:2]]
                    c, image = item.get("classification", {}), item.get("image_metadata", {})
                    return (c.get("excluido", False), c.get("versao_comercial") == "promocional", c.get("requires_conversion", False),
                            -(image.get("width", 0) * image.get("height", 0)), reference[:2])
                rows.append({"kind": kind, "key": str(key), "references": references,
                             "preferred": min(references, key=publication_rank) if kind != "NAME_SIZE" else None,
                             "decision": "MESMO_ARQUIVO_ORIGENS_PRESERVADAS" if kind != "NAME_SIZE" else "POTENTIAL_DUPLICATE_REVIEW"})
    return rows
