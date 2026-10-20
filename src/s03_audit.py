"""Auditoria reexecutável, sem escrita nas fontes homologadas da S02 (#61)."""

import json
from collections import Counter
from pathlib import Path

import numpy as np

from .agreement import apply_resolutions, build_votes
from .gold_sample import CATEGORIES, RATERS, read_csv, sha256, timestamp
from .label_validation import load_sample, public_result, validate_labels
from .s02_quality import audit as audit_dataset
from . import corrective

HUMAN_HASHES = {
    "islayder": "9cb894ee51a8cfde238dbd3e978064d4ccfc159812f94449b391342419811a51",
    "fernanda": "f0b3bca6461306a6c3695538a152213b7991215610f200f17c29417625a00cfb",
    "vinicius": "370fb02756ca4d10141a90857f60600885558fb4a975f6fd976edc3475d8eb9d",
}


def independent_kappa(votes):
    """Fleiss pela fórmula de contagens; não chama statsmodels/agreement."""
    counts = [Counter(row) for row in votes]
    observed = np.mean([sum(v * (v - 1) for v in c.values()) / 6 for c in counts])
    totals = sum(counts, Counter())
    expected = sum((v / (len(votes) * 3)) ** 2 for v in totals.values())
    return None if expected == 1 else float((observed - expected) / (1 - expected))


def independent_cfr(predictions, details, end):
    """Prefixos/searchsorted para verificar cada evento, sem usar CFR.calculate."""
    expected = {(r["full_name"], r["release_id"]): r["status"] for r in details}
    groups = {}
    for row in predictions:
        groups.setdefault(row["full_name"], []).append(row)
    statuses = Counter()
    for name, rows in groups.items():
        rows.sort(key=lambda r: (timestamp(r["published_at"]), int(r["release_id"])))
        times = np.array([timestamp(r["published_at"]).timestamp() for r in rows])
        positive = np.array([r["classification_usable"] == "True" and r["corrective_release"] == "yes" for r in rows], int)
        unknown = np.array([r["classification_usable"] == "False" for r in rows], int)
        p, u = np.r_[0, np.cumsum(positive)], np.r_[0, np.cumsum(unknown)]
        left = np.searchsorted(times, times, side="right")
        right = np.searchsorted(times, times + 7 * 86400, side="right")
        for i, row in enumerate(rows):
            state = ("right_censored" if times[i] >= end - 7 * 86400 else "failed" if p[right[i]] > p[left[i]]
                     else "unassessable_context" if u[right[i]] > u[left[i]] else "not_failed")
            if expected.pop((name, row["release_id"])) != state:
                raise ValueError("CFR(b) diverge da recomputação independente.")
            statuses[state] += 1
    if expected:
        raise ValueError("Eventos CFR(b) sem previsão correspondente.")
    return dict(statuses)


def run(root=Path(".")):
    gold, folder = root / "data/gold_sample", root / "data/processed/s02"
    sample = load_sample(gold / "gold_sample.csv")
    validations = {}
    for rater in RATERS:
        path = gold / f"gold_sample_{rater}.csv"
        if sha256(path) != HUMAN_HASHES[rater]:
            raise ValueError(f"Rotulagem homologada mudou: {rater}")
        validations[rater] = validate_labels(path, sample)
        if not validations[rater]["complete"]:
            raise ValueError("Rotulagem incompleta.")
    votes = build_votes(sample, {r: v["rows"] for r, v in validations.items()})
    resolved = apply_resolutions(votes, gold / "manual_resolutions.csv")
    consensus = {r["item_id"]: r for r in read_csv(gold / "gold_sample_consensus.csv")}
    for row in resolved:
        targets = [r for r in consensus.values() if (r["item_id"] if row["dimension"] == "corrective_release" else r["repository"].casefold()) == row["item_id"]]
        if row["needs_manual_review"] or not targets or any(r[row["dimension"]] != row["consensus"] for r in targets):
            raise ValueError("Consenso difere dos votos e da resolução humana.")
    kappas = {dimension: independent_kappa([[row[f"{r}_label"] for r in RATERS] for row in votes if row["dimension"] == dimension]) for dimension in CATEGORIES}
    for row in read_csv(root / "data/validation/fleiss_kappa.csv"):
        if not np.isclose(float(row["kappa"]), kappas[row["dimension"]]):
            raise ValueError("Kappa publicado difere da fórmula independente.")
    evaluations = []
    for version in ("v1", "v2", "v3", "v4", "v5"):
        directory = root / "data/validation/corrective" / version
        evaluation = json.loads((directory / "evaluation.json").read_text(encoding="utf-8"))
        if sha256(directory / "predictions.csv") != evaluation["predictions_sha256"] or sha256(directory / "corrective.py.txt") != evaluation["implementation_sha256"]:
            raise ValueError("Hash de avaliação/predição/snapshot divergente.")
        for source in evaluation["sources"]:
            if sha256(root / source["path"].replace("\\", "/")) != source["sha256"]:
                raise ValueError("Fonte da avaliação foi alterada.")
        counts = Counter()
        for row in read_csv(directory / "predictions.csv"):
            truth = consensus[row["item_id"]]["corrective_release"] == "yes"
            predicted = row["corrective_release"] == "yes"
            counts["tp" if truth and predicted else "fn" if truth else "fp" if predicted else "tn"] += 1
        if any(counts[key] != evaluation[key] for key in ("tp", "fp", "fn", "tn")):
            raise ValueError("Matriz de confusão diverge do consenso verdadeiro.")
        tp, fp, fn = (counts[key] for key in ("tp", "fp", "fn"))
        derived = dict(precision=tp / (tp + fp), recall=tp / (tp + fn), f1=2 * tp / (2 * tp + fp + fn))
        if any(not np.isclose(derived[key], evaluation[key]) for key in derived):
            raise ValueError("Precision/recall/F1 divergem da matriz de confusão.")
        evaluations.append({"version": version, **dict(counts), "f1": evaluation["f1"], "status": evaluation["status"]})
    if (evaluations[-1]["status"] != "accepted" or evaluations[-1]["f1"] < .7
            or Path(corrective.__file__).read_bytes().replace(b"\r\n", b"\n") != (root / "data/validation/corrective/v5/corrective.py.txt").read_bytes().replace(b"\r\n", b"\n")):
        raise ValueError("A implementação atual não corresponde à v5 aceita.")
    profile = audit_dataset(folder)
    if profile["errors"]:
        raise ValueError("Dataset S02 falhou na auditoria.")
    predictions = read_csv(folder / "corrective_v5/release_predictions.csv")
    population = json.loads((folder / "corrective_v5/manifest.json").read_text(encoding="utf-8"))
    if sha256(folder / "corrective_v5/release_predictions.csv") != population["predictions_sha256"]:
        raise ValueError("População corretiva diverge do manifesto homologado.")
    statuses = independent_cfr(predictions, read_csv(folder / "cfr_delivery_releases_s02.csv"), timestamp("2026-10-01T00:00:00Z").timestamp())
    protected = sorted([*gold.glob("*.csv"), *folder.rglob("*")])
    sources = [{"path": p.relative_to(root).as_posix(), "sha256": sha256(p)} for p in protected if p.is_file()]
    decision_counts = Counter("unanimous" if len({r[f"{v}_label"] for v in RATERS}) == 1 else
                              "manual" if r["needs_manual_review"] else "majority" for r in votes)
    return {"status": "valid", "human_hashes": HUMAN_HASHES, "consensus_sha256": sha256(gold / "gold_sample_consensus.csv"),
            "validations": {r: public_result(v) for r, v in validations.items()}, "fleiss_kappa": kappas,
            "consensus_pending": 0, "original_decisions": dict(decision_counts), "evaluations": evaluations, "independent_cfr_statuses": statuses,
            "dataset": profile, "protected_sources": sources}
