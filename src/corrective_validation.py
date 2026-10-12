"""#58: avaliação offline contra consenso, depois da rotulagem de Fernanda."""

from __future__ import annotations

import argparse
import csv
import gzip
import json
import platform
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from .corrective import POLICIES, predict
from .gold_sample import boolean, sha256, timestamp
from .label_validation import load_sample, validate_labels
from .pipeline import write_csv


def previous_tags(releases_path: Path, predecessors_path: Path, sample: dict) -> dict[str, str]:
    """Usa todas as releases estáveis, nunca apenas as cinco sorteadas."""
    names = {row["repository"].casefold() for row in sample.values()}
    grouped, seen = defaultdict(list), {}
    for path in (releases_path, predecessors_path):
        opener = gzip.open if path.suffix == ".gz" else Path.open
        with opener(path, "rt", encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle)
            if not {"full_name", "release_id", "tag_name", "published_at", "prerelease"}.issubset(reader.fieldnames or []):
                raise ValueError(f"Histórico de releases inválido: {path}")
            for row in reader:
                name = row["full_name"].casefold()
                if name not in names:
                    continue
                is_prerelease = boolean(row["prerelease"])
                key = (name, row["release_id"])
                signature = (row["tag_name"], timestamp(row["published_at"]), is_prerelease)
                if key in seen:
                    if seen[key] != signature:
                        raise ValueError(f"Release conflitante no histórico: {key}")
                    # O snapshot principal já inclui alguns predecessores.
                    continue
                seen[key] = signature
                if is_prerelease:
                    continue
                grouped[name].append(row)
    result = {}
    for name, rows in grouped.items():
        rows.sort(key=lambda r: (timestamp(r["published_at"]), int(r["release_id"])))
        for index, row in enumerate(rows):
            identifier = f"{name}::release::{row['release_id']}"
            if identifier not in sample:
                continue
            canonical = sample[identifier]
            if row["tag_name"] != canonical["tag_name"] or timestamp(row["published_at"]) != timestamp(canonical["published_at"]):
                raise ValueError(f"Histórico desalinhado: {identifier}")
            result[identifier] = rows[index - 1]["tag_name"] if index else ""
    if set(result) != set(sample):
        raise ValueError("Histórico não contém todas as releases da amostra.")
    return result


def scores(truth: list[str], predicted: list[str]) -> dict:
    """Classe positiva = yes; zeros indefinidos são registrados explicitamente."""
    from sklearn.metrics import precision_recall_fscore_support

    if not truth or len(truth) != len(predicted) or any(v not in ("yes", "no") for v in (*truth, *predicted)):
        raise ValueError("Avaliação exige pares yes/no não vazios e alinhados.")
    precision, recall, f1, _ = precision_recall_fscore_support(
        truth, predicted, average="binary", pos_label="yes", zero_division=0)
    tp = sum(a == b == "yes" for a, b in zip(truth, predicted))
    fp = sum(a == "no" and b == "yes" for a, b in zip(truth, predicted))
    fn = sum(a == "yes" and b == "no" for a, b in zip(truth, predicted))
    tn = len(truth) - tp - fp - fn
    status = "unassessable_no_positive_consensus" if tp + fn == 0 else "accepted" if f1 >= .70 else "needs_refinement"
    return {"items": len(truth), "positive_label": "yes", "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": float(precision), "recall": float(recall), "f1": float(f1),
            "precision_defined": tp + fp > 0, "recall_defined": tp + fn > 0,
            "f1_defined": 2 * tp + fp + fn > 0, "threshold": .70, "status": status}


def evaluate(sample_path: Path, fernanda_path: Path, consensus_path: Path, releases_path: Path,
             predecessors_path: Path, output_dir: Path, version: str = "v1") -> dict:
    if version not in POLICIES:
        raise ValueError(f"Versão desconhecida: {version}")
    if fernanda_path.name != "gold_sample_fernanda.csv":
        raise ValueError("Informe a rotulagem independente de Fernanda.")
    inputs = (sample_path, fernanda_path, consensus_path, releases_path, predecessors_path)
    if len({p.resolve() for p in inputs}) != len(inputs):
        raise ValueError("Amostra, rotulagem, consenso e históricos devem ser arquivos distintos.")
    if consensus_path.name != "gold_sample_consensus.csv":
        raise ValueError("Informe gold_sample_consensus.csv produzido após a #57.")
    if output_dir.exists():
        raise ValueError("Use uma pasta nova por avaliação para preservar cada versão e resultado.")
    sample = load_sample(sample_path)
    if not validate_labels(fernanda_path, sample)["complete"]:
        raise ValueError("Conclua primeiro a rotulagem independente de Fernanda; nenhuma previsão foi gerada.")
    consensus = validate_labels(consensus_path, sample)
    if not consensus["complete"]:
        raise ValueError("Consenso da #57 ausente, incompleto ou desalinhado; nenhuma previsão foi gerada.")
    # Fingerprints antes da análise; a saída conserva a implementação avaliada.
    sources = [{"path": str(path), "sha256": sha256(path)} for path in inputs]
    predecessor = previous_tags(releases_path, predecessors_path, sample)
    rows = []
    for identifier, row in sample.items():
        commits = json.loads(row["commits_context"] or "[]")
        if not isinstance(commits, list) or any(not isinstance(c, dict) or not isinstance(c.get("message"), str) for c in commits):
            raise ValueError(f"Contexto de commits inválido: {identifier}")
        prediction = predict(tag=row["tag_name"], previous_tag=predecessor[identifier], body=row["release_body"],
                             messages=[c["message"] for c in commits], interval_status=row["interval_status"], version=version)
        rows.append({"item_id": identifier, "repository": row["repository"], "release_id": row["release_id"],
                     "tag_name": row["tag_name"], "previous_tag": predecessor[identifier],
                     "consensus": consensus["rows"][identifier]["corrective_release"], **prediction.to_dict()})
    result = scores([r["consensus"] for r in rows], [r["corrective_release"] for r in rows])
    import sklearn
    source_path = Path(__file__).with_name("corrective.py")
    result.update(version=version, policy=POLICIES[version], sources=sources,
                  evaluated_at=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
                  sklearn=sklearn.__version__, implementation_sha256=sha256(source_path),
                  incomplete_commit_context=sum(not r["commit_context_complete"] for r in rows),
                  limitations=["Heurística identifica sinais; não prova causalidade nem defeito recente.",
                               "Reavaliações na mesma amostra são validação interna, sem teste externo independente."])
    if any(sha256(Path(s["path"])) != s["sha256"] for s in sources):
        raise ValueError("Entrada mudou durante a avaliação; execute novamente.")
    output_dir.mkdir(parents=True, exist_ok=False)
    write_csv(output_dir / "predictions.csv", tuple(rows[0]), rows)
    result["predictions_sha256"] = sha256(output_dir / "predictions.csv")
    (output_dir / "corrective.py.txt").write_bytes(source_path.read_bytes())
    (output_dir / "evaluation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (output_dir / "report.md").write_text(
        f"# #58 — heurística {version}\n\n{POLICIES[version]}\n\n"
        f"{len(rows)} releases; precisão {result['precision']:.4f}; recall {result['recall']:.4f}; F1 {result['f1']:.4f}.\n\n"
        f"Status: {result['status']}. Limiar: 0,70 (comparação sem arredondamento).\n\n"
        f"TP={result['tp']}; FP={result['fp']}; FN={result['fn']}; TN={result['tn']}.\n"
        f"Contexto de commits incompleto: {result['incomplete_commit_context']}.\n\n"
        "Confira no JSON os casos de métricas indefinidas. F1 abaixo de 0,70 exige refinamento e nova avaliação.\n"
        "Preserve esta pasta; não escolha uma versão pela acurácia nem substitua o consenso pelos votos de uma pessoa.\n",
        encoding="utf-8")
    return result


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="#58 — validação de release corretiva contra consenso humano")
    parser.add_argument("--sample", type=Path, default=Path("data/gold_sample/gold_sample.csv"))
    parser.add_argument("--fernanda", type=Path, default=Path("data/gold_sample/gold_sample_fernanda.csv"))
    parser.add_argument("--consensus", type=Path, default=Path("data/gold_sample/gold_sample_consensus.csv"))
    parser.add_argument("--releases", type=Path, default=Path("data/processed/s02/releases_s01.csv.gz"))
    parser.add_argument("--predecessors", type=Path, default=Path("data/processed/s02/release_predecessors_s02.csv"))
    parser.add_argument("--version", choices=tuple(POLICIES), default="v1")
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = evaluate(args.sample, args.fernanda, args.consensus, args.releases, args.predecessors,
                          args.output_dir, args.version)
    except (OSError, ValueError, KeyError, TypeError) as error:
        print(f"Não avaliado: {error}")
        return 1
    print(f"{result['version']}: P={result['precision']:.4f}; R={result['recall']:.4f}; F1={result['f1']:.4f}; {result['status']}")
    return 0 if result["status"] == "accepted" else 2


if __name__ == "__main__":
    raise SystemExit(main())
