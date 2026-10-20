"""Execução offline auditável da Sprint 03; coleta complementar é etapa separada (#72)."""

import argparse
import importlib.metadata
import hashlib
import json
import platform
from pathlib import Path

import pandas as pd

from . import s03_audit, s03_bootstrap, s03_descriptive, s03_figures, s03_inference, s03_sensitivity
from .gold_sample import read_csv, sha256
from .s03_collect import save


def run(output=Path("data/processed/s03"), reports=Path("reports/s03"), figures=Path("figures/s03"), *, core_only=False, permutations=9999, iterations=2000):
    audit = s03_audit.run()
    save(reports / "audit.json", audit)
    data = s03_descriptive.load_data(Path("data/processed/s02/dataset_final_s02.csv"))
    output.mkdir(parents=True, exist_ok=True)
    descriptions, classes, distribution = s03_descriptive.run(data)
    correlations, factors, groups, cuts = s03_inference.run(data, permutations)
    bootstrap = s03_bootstrap.run(data, iterations)
    rework = s03_sensitivity.rework(read_csv(Path("data/processed/s02/corrective_v5/release_predictions.csv")))
    outputs = dict(descriptive=descriptions, classifications=classes, dora_distribution=distribution,
        spearman=correlations, factor_tests=factors, factor_groups=groups, factor_cutpoints=cuts,
        bootstrap=bootstrap, rework=rework,
        rework_summary=pd.DataFrame([{"metric": "rework_rate", "unit": "fraction", **s03_descriptive.describe(rework.rework_rate)}]))
    variant_classes = None
    if not core_only:
        variants, variant_classes, comparisons, predictions, details, provenance = s03_sensitivity.run(data, classes, output)
        outputs.update(variant_metrics=variants, variant_classifications=variant_classes, sensitivity=comparisons,
                       c2_predictions=predictions, c2_cfr_events=details, comparisons_provenance=provenance)
        common = variant_classes[[f"{v}_general" for v in ("C1", "C2", "C3")]].notna().all(axis=1)
        outputs["sensitivity_common"] = s03_sensitivity.compare_classifications(variant_classes.loc[common])
        exclusions = []
        for left, right in (("C1", "C2"), ("C1", "C3"), ("C2", "C3")):
            for _, row in variant_classes.iterrows():
                if pd.isna(row[f"{left}_general"]) or pd.isna(row[f"{right}_general"]):
                    exclusions.append(dict(full_name=row.full_name, left=left, right=right,
                        missing_left=pd.isna(row[f"{left}_general"]), missing_right=pd.isna(row[f"{right}_general"])))
        outputs["sensitivity_exclusions"] = pd.DataFrame(exclusions, columns=["full_name", "left", "right", "missing_left", "missing_right"])
    for name, frame in outputs.items():
        frame.to_csv(output / (name + ".csv"), index=False, lineterminator="\n", float_format="%.15g")
    s03_figures.run(data, descriptions, distribution, correlations, bootstrap, rework, figures, variant_classes)
    for source in audit["protected_sources"]:
        if sha256(Path(source["path"])) != source["sha256"]:
            raise ValueError("Fonte homologada mudou durante a execução.")
    sources = audit["protected_sources"]
    if not core_only:
        for path in [output / "variant_plan.json.gz", *sorted((output / "variant_context").glob("part-*.jsonl.gz"))]:
            sources.append({"path": path.as_posix(), "sha256": sha256(path)})
    manifest = {"status": "core_complete_rq07_pending" if core_only else "analyses_executed",
        "window": {"start_date": "2025-10-01", "end_date": "2026-10-01", "end_exclusive": True},
        "repositories": len(data), "seed": 42, "bootstrap_iterations": iterations, "permutations": permutations,
        "python": platform.python_version(),
        "versions": {p: importlib.metadata.version(p) for p in ("numpy", "scipy", "pandas", "statsmodels", "scikit-learn", "matplotlib")},
        "sources": sources, "implementation_hash_policy": "UTF-8 bytes with CRLF normalized to LF",
        "implementation": [{"path": p.as_posix(), "sha256": hashlib.sha256(p.read_bytes().replace(b"\r\n", b"\n")).hexdigest()} for p in sorted(Path("src").glob("s03*.py"))],
        "figures": [{"path": p.as_posix(), "sha256": sha256(p)} for p in sorted(figures.glob("*")) if p.suffix in (".png", ".svg", ".pdf")],
        "outputs": [{"path": (output / (n + ".csv")).as_posix(), "sha256": sha256(output / (n + ".csv"))} for n in outputs]}
    save(reports / "manifest.json", manifest)
    print(json.dumps({"status": manifest["status"], "repositories": len(data), "outputs": len(outputs)}, ensure_ascii=False))
    return manifest


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("data/processed/s03"))
    parser.add_argument("--reports", type=Path, default=Path("reports/s03"))
    parser.add_argument("--figures", type=Path, default=Path("figures/s03"))
    parser.add_argument("--core-only", action="store_true", help="Executa RQ01–06, inovação e RQ08 enquanto RQ07 coleta.")
    args = parser.parse_args(argv)
    run(args.output, args.reports, args.figures, core_only=args.core_only)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
