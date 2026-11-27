"""Amostragem determinística e métricas somente após homologação humana."""

from collections import Counter, defaultdict
import csv
import hashlib
import re
from pathlib import Path

from .audit_report import CATEGORIES

LABELS = (*CATEGORIES, "DESCARTADO")


def write_sample(path, inventories, per_stratum=3):
    strata = defaultdict(list)
    for source, _, files in inventories:
        for item in files:
            c = item["classification"]
            strata[(source.pasta_id, c.get("categoria") or "sem_categoria", c["status_decisao"])].append((source, item))
    headers = ["source_id", "drive_file_id", "nome", "caminho", "mime_type", "categoria_motor", "decisao_motor", "motivo_motor", "categoria_humana", "observacao_humana"]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for _, entries in sorted(strata.items()):
            entries.sort(key=lambda entry: hashlib.sha256((entry[0].pasta_id + entry[1]["id"]).encode()).hexdigest())
            # Arquivos sem categoria e imagens com palavras explícitas têm
            # prioridade dentro do estrato de revisão, sem definir ground truth.
            entries.sort(key=lambda entry: not bool(re.search(r"fachada|piscina|academia|sala|cozinha|tabela", entry[1]["name"], re.I)))
            for source, item in entries[:per_stratum]:
                c = item["classification"]
                prediction = c["categoria"] if c.get("categoria") and not c["excluido"] else c["status_decisao"]
                from .report import safe_text
                writer.writerow([safe_text(value) for value in [source.pasta_id, item["id"], item["name"], item["folder_path"], item["mime_type"], prediction, c["status_decisao"], c["motivo"], "", ""]])


def evaluate_sample(path):
    matrix, seen = Counter(), set()
    unlabelled = 0
    with Path(path).open(encoding="utf-8-sig", newline="") as handle:
        for row in csv.DictReader(handle):
            key = row["source_id"], row["drive_file_id"]
            if key in seen:
                raise ValueError("Amostra contém chave duplicada (fonte, arquivo).")
            seen.add(key)
            gold = row["categoria_humana"].strip()
            if not gold:
                unlabelled += 1
                continue
            if gold not in LABELS or row["categoria_motor"] not in (*LABELS, "REVISAO"):
                raise ValueError("Categoria inválida. Utilize tabela_precos, fachada, lazer, internos ou DESCARTADO.")
            matrix[(gold, row["categoria_motor"]) ] += 1
    if not matrix:
        raise ValueError("Nenhum arquivo homologado. Preencha categoria_humana antes de calcular métricas.")
    scores = {}
    for label in LABELS:
        tp = matrix[(label, label)]
        fp = sum(count for (gold, prediction), count in matrix.items() if prediction == label and gold != label)
        fn = sum(count for (gold, prediction), count in matrix.items() if gold == label and prediction != label)
        precision, recall = tp / (tp + fp) if tp + fp else 0, tp / (tp + fn) if tp + fn else 0
        scores[label] = {"precision": precision, "recall": recall, "f1": 2 * precision * recall / (precision + recall) if precision + recall else 0, "support": tp + fn}
    supported = [score for score in scores.values() if score["support"]]
    return {"labelled": sum(matrix.values()), "unlabelled": unlabelled, "per_category": scores,
            "macro_f1_supported": sum(score["f1"] for score in supported) / len(supported),
            "confusion_matrix": [{"human": gold, "predicted": prediction, "count": count} for (gold, prediction), count in sorted(matrix.items())],
            "limitation": "Amostra estratificada; métricas da amostra, sem estimativa não ponderada da população. REVISAO é abstenção e conta como erro/omissão frente ao rótulo humano."}
