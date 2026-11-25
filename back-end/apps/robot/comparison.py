"""Comparação por (folder_id da fonte, file_id), sem depender do nome."""

from collections import Counter, defaultdict

from openpyxl import Workbook, load_workbook

from .audit_report import CATEGORIES, candidate, compact, metrics
from .profiles import IMAGE_MIMES, contains, get_profile, normalize
from .report import add_sheet, atomic_save


def baseline_records(path):
    book = load_workbook(path, read_only=True, data_only=True)
    try:
        sources = defaultdict(list)
        for row in book["Fontes"].iter_rows(min_row=2, values_only=True):
            sources[row[0]].append(row[1])
        headers = [cell.value for cell in next(book["Arquivos"].iter_rows())]
        records = {}
        for row in book["Arquivos"].iter_rows(min_row=2, values_only=True):
            if len(row) < 18:
                raise ValueError("Use um mapa filtrado como baseline, com colunas de categoria e identidade.")
            extra = dict(zip(headers, row))
            source_id = extra.get("source_id")
            if not source_id:
                if len(sources[row[0]]) != 1:
                    raise ValueError("Baseline com nome de fonte ambíguo e sem source_id.")
                source_id = sources[row[0]][0]
            records[(source_id, row[6])] = {"name": row[2], "size": row[4] or 0, "project": row[9] or "",
                "companies": row[10] or "", "identity_confidence": row[11], "category": row[12], "score": row[13], "review": row[14]}
        return records
    finally:
        book.close()


def compare(path, inventories):
    old = baseline_records(path)
    all_items = {(source.pasta_id, item["id"]): item for source, _, files in inventories for item in files}
    if set(old) - set(all_items):
        raise ValueError("A baseline contém arquivos fora do universo V2. Use o mesmo inventário e as mesmas fontes.")
    new = {key: item for key, item in all_items.items() if candidate(item)}
    old_categories = Counter(record["category"] for record in old.values())
    new_categories = Counter(item["classification"]["categoria"] for item in new.values())
    changes = []
    for key, item in sorted(all_items.items()):
        previous = old.get(key)
        current = new.get(key)
        c, identity = item["classification"], item.get("project_identity", {})
        flags = []
        if previous is None and current is not None:
            flags.append("RECUPERADO")
        if previous is not None and current is None:
            flags.append("NAO_SELECIONADO_V2")
        if previous and current:
            if previous["category"] != c["categoria"]:
                flags.append("CATEGORIA_ALTERADA")
            if normalize(previous["project"]) != normalize(identity.get("name", "")):
                flags.append("EMPREENDIMENTO_ALTERADO")
            old_companies = sorted(part.strip() for part in previous["companies"].split(";") if part.strip())
            if old_companies != sorted(identity.get("companies", [])):
                flags.append("CONSTRUTORA_ALTERADA")
        if flags:
            changes.append([*key, item["name"], "; ".join(flags), previous["category"] if previous else "", c["categoria"],
                            previous["project"] if previous else "", identity.get("name", ""), previous["companies"] if previous else "", compact(identity.get("companies", [])),
                            previous["score"] if previous else None, c["pontuacao"], compact(c.get("regras", [])), c["motivo"], c["status_decisao"]])
    m = metrics(inventories)
    org = {"tabelas comerciais", "black drx 2026", "tabelas"}
    old_wrong = sum(r["category"] == "tabela_precos" and normalize(r["project"]) in org for r in old.values())
    new_wrong = sum(item["classification"]["categoria"] == "tabela_precos" and normalize(item.get("project_identity", {}).get("name", "")) in org for item in new.values())
    pairs = [("Arquivos originais", len(all_items), len(all_items)), ("Candidatos categorizados (inclui revisão)", len(old), len(new)),
             ("Não candidatos", len(all_items) - len(old), len(all_items) - len(new)),
             *[(category, old_categories[category], new_categories[category]) for category in CATEGORIES],
             ("Tabelas com identidade organizacional", old_wrong, new_wrong),
             ("Identidade construtora não resolvida ou em revisão (candidatos)", sum(r["identity_confidence"] != "alta" for r in old.values()),
              sum(item.get("project_identity", {}).get("developer_confidence", {}).get("revisao", True) for item in new.values())),
             ("Bytes candidatos conhecidos", sum(r["size"] for r in old.values()), m["bytes_candidatos"]),
             ("Recuperados", 0, len(new.keys() - old.keys())), ("Anteriormente selecionados, agora não candidatos", 0, len(old.keys() - new.keys()))]
    source_rows = []
    recovery_rows = []
    for source, _, files in inventories:
        before = [r for (sid, _), r in old.items() if sid == source.pasta_id]
        after = [item for item in files if candidate(item)]
        source_rows.append([source.pasta_id, source.nome, len(files), len(before), len(after), len(after) - len(before),
                            *[sum(r["category"] == category for r in before) for category in CATEGORIES],
                            *[sum(item["classification"]["categoria"] == category for item in after) for category in CATEGORIES]])
        profile = get_profile(source)
        if profile and profile.config["code"] in ("BASE-01", "BASE-02", "01", "06", "10"):
            keywords = [word for category, rule in profile.config["categories"].items() if category != "tabela_precos" for word in rule["keywords"]]
            keywords += [word for values in profile.config.get("keyword_aliases", {}).values() for word in values]
            for item in files:
                if (source.pasta_id, item["id"]) in old or item["mime_type"] not in IMAGE_MIMES:
                    continue
                hits = [word for word in keywords if contains(item["name"], word)]
                if not hits:
                    continue
                relative = "/".join(item["folder_path"].split("/")[1:])
                old_reason = next((word for word in profile.config["exclude"] if contains(relative + "/" + item["name"], word)), "sem correspondência inequívoca nas regras V1")
                c = item["classification"]
                recovery_rows.append([source.pasta_id, item["id"], item["name"], item["folder_path"], compact(hits), old_reason,
                                      candidate(item), c["categoria"], c["status_decisao"], c["motivo"], compact(c.get("evidencias", []))])
    targets = {normalize(value) for value in ("TABELA MAKAI", "TABELA ESSENZA PARK", "Elevare - Tabela de Vendas - 2026.11", "TABELA MONDO", "Tabela Lumini", "Tabela Soho", "TABELA SOLEIL", "Tabela Sens")}
    mga_id = next((source.pasta_id for source, _, _ in inventories if get_profile(source) and get_profile(source).config["code"] == "BASE-02"), None)
    audited_tables = [(key, item) for key, item in all_items.items() if key[0] == mga_id and normalize(item["name"]) in targets]
    pairs.append(("Tabelas MGA explicitamente omitidas (8 alvos)", sum(key not in old for key, _ in audited_tables), sum(key not in new for key, _ in audited_tables)))
    pairs.append(("Alvos MGA encontrados no universo", len(audited_tables), len(audited_tables)))
    regressions = [[*key, item["name"], key in old, candidate(item), item.get("project_identity", {}).get("name", ""), item["classification"]["motivo"]] for key, item in audited_tables]
    return {"metrics": pairs, "changes": changes, "sources": source_rows, "summary": m, "recovery": recovery_rows, "regressions": regressions}


def write_comparison(output, baseline, inventories):
    result = compare(baseline, inventories)
    book = Workbook()
    book.remove(book.active)
    add_sheet(book, "Comparativo", ["Indicador", "V1", "V2", "Variação"], [[name, old, new, new - old] for name, old, new in result["metrics"]], [80, 25, 25, 25])
    add_sheet(book, "Mudanças", ["source_id", "drive_file_id", "Nome", "Mudanças", "Categoria V1", "Categoria V2", "Empreendimento V1", "Empreendimento V2", "Construtoras V1", "Construtoras V2", "Pontuação V1", "Pontuação V2", "Regras V2", "Motivo V2", "Status V2"], result["changes"], [42, 42, 60, 60] + [35] * 11)
    add_sheet(book, "Por fonte", ["source_id", "Fonte", "Originais", "Candidatos V1", "Candidatos V2", "Variação", *[f"V1 {c}" for c in CATEGORIES], *[f"V2 {c}" for c in CATEGORIES]], result["sources"], [45, 35] + [24] * 12)
    add_sheet(book, "Recuperação auditada", ["source_id", "drive_file_id", "Nome", "Caminho", "Palavras explícitas", "Hipótese de descarte V1 (regra reproduzida)", "Candidato V2", "Categoria V2", "Status V2", "Motivo V2", "Evidências V2"], result["recovery"], [45, 45, 65, 90, 45, 55, 22, 25, 25, 40, 120])
    add_sheet(book, "Regressões P0", ["source_id", "drive_file_id", "Nome", "Candidato V1", "Candidato V2", "Empreendimento V2", "Motivo V2"], result["regressions"], [45, 45, 65, 22, 22, 40, 45])
    add_sheet(book, "Método", ["Campo", "Valor"], [
        ["Baseline", str(baseline)], ["Chave", "source_folder_id + drive_file_id"],
        ["Seleção comparável", "Candidatos categorizados, incluindo revisão, como no V1"],
        ["Decisões V2", "SELECIONADO + DESCARTADO + REVISAO = originais; revisão não equivale a descarte"],
        ["Qualidade", "Retenção não é acurácia. Sem ground truth não há precisão/recall/F1."],
        ["Pontuações", "Escalas heurísticas alteradas; variação não mede ganho estatístico de qualidade."],
        ["145 candidatos citados", "A lista original de IDs dos 145 não foi fornecida. Todos os originais foram reavaliados. A aba Recuperação auditada usa critério explícito e reprodutível, sem forçar esse total."],
    ], [35, 120])
    atomic_save(book, output)
    return result
