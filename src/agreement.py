"""Concordância e consenso; nunca preenche avaliações humanas (#57)."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from .gold_sample import CATEGORIES, CONTEXT_FIELDS, LABEL_FIELDS, RATERS, read_csv, sha256
from .label_validation import load_sample, public_result, validate_labels
from .pipeline import write_csv

VOTE_FIELDS = ("item_id", "repository", "release", "dimension", "islayder_label",
               "fernanda_label", "vinicius_label", "consensus", "needs_manual_review")
RESOLUTION_FIELDS = ("item_id", "dimension", "consensus", "reviewer", "notes")
KAPPA_FIELDS = ("dimension", "items", "raters", "kappa", "interpretation", "status")


def interpretation(value: float) -> str:
    if value < 0:
        return "pobre"
    for upper, label in ((0.2, "leve"), (0.4, "razoável"), (0.6, "moderada"),
                         (0.8, "substancial"), (1.000000000001, "quase perfeita")):
        if value <= upper:
            return label
    raise ValueError("Kappa fora do intervalo.")


def kappa_result(votes: list[list[str]], dimension: str) -> dict:
    import numpy as np
    from statsmodels.stats.inter_rater import aggregate_raters, fleiss_kappa

    categories = CATEGORIES[dimension]
    if not votes or any(len(row) != 3 or any(label not in categories for label in row) for row in votes):
        raise ValueError("Kappa exige três votos válidos por item.")
    codes = [[categories.index(label) for label in row] for row in votes]
    table, _ = aggregate_raters(codes, n_cat=len(categories))
    # Pe=1 torna o denominador zero. Não apresentar nan nem inventar kappa=1.
    constant = np.count_nonzero(table.sum(axis=0)) == 1
    value = None if constant else float(fleiss_kappa(table, method="fleiss"))
    return {"dimension": dimension, "items": len(votes), "raters": 3,
            "kappa": "" if value is None else value,
            "interpretation": "indefinido (uma única categoria observada)" if value is None else interpretation(value),
            "status": "undefined_constant_category" if constant else "calculated"}


def vote_consensus(votes: list[str]) -> tuple[str, bool]:
    if len(votes) != 3 or any(not label for label in votes):
        raise ValueError("Consenso exige três votos preenchidos.")
    label, count = Counter(votes).most_common(1)[0]
    return (label, False) if count >= 2 else ("", True)


def build_votes(sample: dict[str, dict], ratings: dict[str, dict]) -> list[dict]:
    result, seen_repos = [], set()
    for identifier, item in sorted(sample.items()):
        name = item["repository"]
        dimensions = ["corrective_release"]
        if name not in seen_repos:
            dimensions += ["project_type", "releases_represent_real_delivery"]
            seen_repos.add(name)
        for dimension in dimensions:
            repo_level = dimension != "corrective_release"
            item_id = name.casefold() if repo_level else identifier
            votes = [ratings[rater][identifier][dimension] for rater in RATERS]
            consensus, manual = vote_consensus(votes)
            result.append(dict(zip(VOTE_FIELDS, (item_id, name, "" if repo_level else item["tag_name"],
                               dimension, *votes, consensus, manual))))
    return result


def apply_resolutions(votes: list[dict], path: Path | None) -> list[dict]:
    result = [dict(row) for row in votes]
    unresolved = {(row["item_id"], row["dimension"]): row for row in result if row["needs_manual_review"]}
    if path is None:
        return result
    seen = set()
    for row in read_csv(path, RESOLUTION_FIELDS, exact=True):
        key = (row["item_id"], row["dimension"])
        if key in seen or key not in unresolved:
            raise ValueError(f"Resolução duplicada ou sem caso manual correspondente: {key}")
        seen.add(key)
        if row["consensus"] not in CATEGORIES[row["dimension"]] or not row["reviewer"].strip() or not row["notes"].strip():
            raise ValueError(f"Resolução exige categoria válida, reviewer e notes: {key}")
        unresolved[key].update(consensus=row["consensus"], needs_manual_review=False)
    return result


def analyze(sample_path: Path, rater_paths: dict[str, Path], output_dir: Path, report: Path,
            resolutions: Path | None = None, consensus_dir: Path | None = None) -> int:
    """Retorna 1 aguardando rótulos, 2 revisão manual pendente, 0 concluído.

    Usa pasta nova para cada execução, preservando resultados anteriores e suas fontes.
    """
    consensus_dir = consensus_dir or output_dir
    derived = [output_dir / "fleiss_kappa.csv",
               consensus_dir / "disagreements.csv", consensus_dir / "consensus_votes.csv",
               consensus_dir / "manual_resolutions_template.csv", consensus_dir / "gold_sample_consensus.csv",
               output_dir / "analysis_status.json"]
    inputs = {path.resolve() for path in (sample_path, *rater_paths.values())}
    if resolutions:
        inputs.add(resolutions.resolve())
    if any(path.resolve() in inputs for path in (*derived, report)):
        raise ValueError("Saídas não podem sobrescrever entradas.")
    if any(path.exists() for path in derived):
        raise ValueError("Execução já existente. Use outro --output-dir para preservar a auditoria.")
    if set(rater_paths) != set(RATERS):
        raise ValueError("Informe Islayder, Fernanda e Vinicius separadamente.")
    if len({path.resolve() for path in rater_paths.values()}) != 3:
        raise ValueError("Arquivos dos avaliadores devem ser independentes.")
    sample = load_sample(sample_path)
    validated = {rater: validate_labels(rater_paths[rater], sample) for rater in RATERS}
    status = {"status": "awaiting_labels", "validation": {r: public_result(v) for r, v in validated.items()},
              "sources": [{"path": str(path), "sha256": sha256(path)} for path in
                          (sample_path, *rater_paths.values()) if path.exists()]}
    lines = ["# Lab03 S02 — validação humana", ""]
    for rater, result in validated.items():
        lines += [f"- {rater}: {result['repositories_evaluated']}/60 repositórios; "
                  f"{result['releases_evaluated']}/300 releases; {len(result['errors'])} erros/pendências."]
    exit_code = 1
    if all(result["complete"] for result in validated.values()):
        votes = build_votes(sample, {r: v["rows"] for r, v in validated.items()})
        kappas = [kappa_result([[row[f"{rater}_label"] for rater in RATERS]
                               for row in votes if row["dimension"] == dimension], dimension)
                  for dimension in CATEGORIES]
        resolved = apply_resolutions(votes, resolutions)
        pending = [row for row in resolved if row["needs_manual_review"]]
        status.update(status="awaiting_manual_consensus" if pending else "complete",
                      unresolved=len(pending), kappa=kappas)
        if resolutions:
            status["sources"].append({"path": str(resolutions), "sha256": sha256(resolutions)})
        write_csv(derived[0], KAPPA_FIELDS, kappas)
        # Divergências preservam os votos e a situação original, antes da discussão.
        write_csv(derived[1], VOTE_FIELDS, [row for row in votes if len({row[f"{r}_label"] for r in RATERS}) > 1])
        write_csv(derived[2], VOTE_FIELDS, resolved)
        write_csv(derived[3], RESOLUTION_FIELDS, [
            {**{key: row[key] for key in ("item_id", "dimension")}, "consensus": "", "reviewer": "", "notes": ""}
            for row in votes if row["needs_manual_review"]])
        if not pending:
            lookup = {(row["item_id"], row["dimension"]): row["consensus"] for row in resolved}
            consolidated = []
            for identifier, item in sample.items():
                labels = {dim: lookup[(identifier if dim == "corrective_release" else item["repository"].casefold(), dim)]
                          for dim in CATEGORIES}
                consolidated.append({**item, **labels, "notes": ""})
            write_csv(derived[4], LABEL_FIELDS, consolidated)
        lines += ["", "Kappa calculado sobre votos originais, anteriores ao consenso:", ""]
        lines += [f"- {row['dimension']}: {row['kappa']} — {row['interpretation']} ({row['items']} itens)." for row in kappas]
        lines += ["", f"Casos aguardando revisão manual: {len(pending)}."]
        exit_code = 2 if pending else 0
    else:
        lines += ["", "Aguardando as rotulagens completas e alinhadas. Kappa, divergências e consenso não calculados.",
                  "Detalhes por linha estão em analysis_status.json."]
    output_dir.mkdir(parents=True, exist_ok=True)
    derived[5].write_text(json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return exit_code
