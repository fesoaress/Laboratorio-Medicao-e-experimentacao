"""Auditoria offline do dataset consolidado; não reescreve dados nem rótulos."""

import argparse
import json
import math
from collections import Counter
from pathlib import Path

from .gold_sample import sha256
from .s02_dataset import (DEPLOYMENT_FIELDS, FUTURE_FIELDS, LEAD_TIME_FIELDS,
                          METADATA_FIELDS, WORKFLOW_FIELDS, index_by_full_name, read_csv)

MAPPINGS = {"deployment_frequency_s02.csv": DEPLOYMENT_FIELDS,
            "lead_time_s01.csv": LEAD_TIME_FIELDS,
            "workflow_metrics_s02.csv": WORKFLOW_FIELDS}
NUMERIC = set(DEPLOYMENT_FIELDS.values()) | set(LEAD_TIME_FIELDS.values()) | set(WORKFLOW_FIELDS.values()) | {"cfr_delivery"}
NUMERIC -= {"lead_time_window_start", "lead_time_window_end"}
COUNTS = {"deployment_frequency_releases", "lead_time_release_count", "lead_time_commit_count",
          "lead_time_releases_without_predecessor", "lead_time_releases_without_new_commits",
          "lead_time_releases_ignored_compare_404", "cfr_ci_successes", "cfr_ci_failures", "cfr_ci_ignored",
          "recovery_time_n_episodes", "recovery_time_n_censored"}
RATIOS = {"cfr_ci", "cfr_delivery", "recovery_time_censored_proportion"}


def audit(folder: Path) -> dict:
    paths = [folder / "dataset_final_s02.csv", folder / "repositories_final_s02.csv",
             *(folder / name for name in MAPPINGS)]
    optional = folder / "cfr_delivery_s02.csv"
    if optional.exists():
        paths.append(optional)
    details_path = folder / "cfr_delivery_releases_s02.csv"
    manifest_path = folder / "cfr_delivery_manifest_s02.json"
    paths += [p for p in (details_path, manifest_path) if p.exists()]
    sources = [{"path": p.as_posix(), "sha256": sha256(p)} for p in paths]
    rows = read_csv(paths[0])
    expected = set(METADATA_FIELDS + FUTURE_FIELDS) | set().union(*(set(m.values()) for m in MAPPINGS.values()))
    if not rows or any(not expected.issubset(row) for row in rows):
        raise ValueError("Dataset vazio ou schema incompleto.")
    errors = []
    identities = [r["full_name"].strip().casefold() for r in rows]
    duplicates = sum(n - 1 for n in Counter(identities).values())
    if duplicates or "" in identities:
        errors.append("Chaves de repositório vazias ou duplicadas.")
    canonical = index_by_full_name(read_csv(paths[1]))
    if set(r["full_name"] for r in rows) != set(canonical):
        errors.append("População difere de repositories_final_s02.csv.")
    joins = {name: index_by_full_name(read_csv(folder / name)) for name in MAPPINGS}
    mappings = dict(MAPPINGS)
    if optional.exists():
        joins[optional.name] = index_by_full_name(read_csv(optional))
        mappings[optional.name] = {"cfr_delivery": "cfr_delivery", "source": "cfr_delivery_source"}
    profile = {field: {"valid": 0, "missing": 0, "invalid": 0} for field in sorted(NUMERIC)}
    missing_reasons = Counter()
    delivery_details = read_csv(details_path) if details_path.exists() else []
    delivery_counts = Counter((r["full_name"], r["status"]) for r in delivery_details)
    if len({(r["full_name"], r["release_id"]) for r in delivery_details}) != len(delivery_details):
        errors.append("Releases duplicadas no detalhamento de CFR(b).")
    for row in rows:
        name = row["full_name"]
        for filename, mapping in mappings.items():
            source = joins[filename].get(name)
            if source is None or any(row[dst] != source.get(src, "") for src, dst in mapping.items()):
                errors.append(f"{name}: fonte ausente ou valor divergente em {filename}.")
        values = {}
        for field in sorted(NUMERIC):
            value = row[field]
            if value == "":
                profile[field]["missing"] += 1
                values[field] = None
                continue
            try:
                number = float(value)
                if not math.isfinite(number) or number < 0 or (field in COUNTS and not number.is_integer()) or (field in RATIOS and number > 1):
                    raise ValueError("fora do domínio")
                values[field] = number
                profile[field]["valid"] += 1
            except ValueError:
                values[field] = None
                profile[field]["invalid"] += 1
                errors.append(f"{name}: tipo/domínio inválido em {field}.")

        def match(field, expected_value):
            actual = values[field]
            if (actual is None) != (expected_value is None) or (actual is not None and not math.isclose(actual, expected_value, rel_tol=1e-8, abs_tol=1e-10)):
                errors.append(f"{name}: fórmula/denominador inconsistente em {field}.")

        successes, failures = values["cfr_ci_successes"], values["cfr_ci_failures"]
        if successes is not None and failures is not None:
            match("cfr_ci", failures / (successes + failures) if successes + failures else None)
        count, days = values["deployment_frequency_releases"], values["deployment_frequency_window_days"]
        if count is not None and days is not None:
            match("deployment_frequency_per_week", count * 7 / days if days else None)
            match("deployment_frequency_per_month", count * 30 / days if days else None)
            if row["release_count"] != row["deployment_frequency_releases"]:
                errors.append(f"{name}: contagem de releases divergente.")
        for variant in ("release", "commit"):
            prefix = f"lead_time_{variant}_"
            q1, median, q3, iqr = (values[prefix + suffix] for suffix in ("q1_hours", "median_hours", "q3_hours", "iqr_hours"))
            if all(v is not None for v in (q1, median, q3, iqr)):
                if not q1 <= median <= q3:
                    errors.append(f"{name}: quartis desordenados ({variant}).")
                match(prefix + "iqr_hours", q3 - q1)
            observations = values[prefix + "count"]
            if (observations is None or observations == 0) != (median is None):
                errors.append(f"{name}: observações/ausência de lead time inconsistentes ({variant}).")
        lead = joins["lead_time_s01.csv"].get(name, {})
        if values["lead_time_release_median_hours"] is None:
            missing_reasons["lead_time:" + lead.get("status", "source_missing")] += 1
        episodes, censored = values["recovery_time_n_episodes"], values["recovery_time_n_censored"]
        if episodes is not None and censored is not None:
            if censored > episodes:
                errors.append(f"{name}: censuras excedem episódios.")
            match("recovery_time_censored_proportion", censored / episodes if episodes else None)
            if (episodes <= censored) != (values["recovery_time_median_hours"] is None):
                errors.append(f"{name}: ausência de recovery incompatível com episódios resolvidos.")
            if values["recovery_time_median_hours"] is None:
                missing_reasons["recovery:no_episodes" if not episodes else "recovery:all_censored"] += 1
        if values["cfr_delivery"] is not None and not row["cfr_delivery_source"]:
            errors.append(f"{name}: CFR(b) sem proveniência.")
        if optional.exists() and name in joins[optional.name]:
            cb = joins[optional.name][name]
            failed, denominator, censored, unavailable = (int(cb[k]) for k in
                ("failed_releases", "evaluable_releases", "right_censored", "unassessable_context"))
            if not (0 <= failed <= denominator) or min(censored, unavailable) < 0 or denominator + censored + unavailable != int(row["release_count"]):
                errors.append(f"{name}: partição/denominador inválido em CFR(b).")
            match("cfr_delivery", failed / denominator if denominator else None)
            if delivery_details and (failed != delivery_counts[name, "failed"]
                    or denominator != failed + delivery_counts[name, "not_failed"]
                    or censored != delivery_counts[name, "right_censored"]
                    or unavailable != delivery_counts[name, "unassessable_context"]):
                errors.append(f"{name}: agregação difere das releases de CFR(b).")
        if values["cfr_delivery"] is None:
            missing_reasons["cfr_delivery:unavailable_see_consensus_and_heuristic_gates"] += 1
    return {"status": "invalid" if errors else "valid_with_pending_cfr_delivery" if profile["cfr_delivery"]["missing"] else "valid",
            "repositories": len(rows), "columns": len(rows[0]), "duplicate_keys": duplicates,
            "metrics": profile, "missing_reasons": dict(missing_reasons), "errors": errors,
            "sources": sources, "cfr_delivery_release_statuses": dict(Counter(r["status"] for r in delivery_details)),
            "scope": "Consolidation, types, formulas and missingness; no new collection or inferred human decisions."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--folder", type=Path, default=Path("data/processed/s02"))
    parser.add_argument("--output", type=Path, default=Path("data/validation/dataset_metrics_audit.json"))
    args = parser.parse_args(argv)
    result = audit(args.folder)
    if args.output.resolve() in {Path(s["path"]).resolve() for s in result["sources"]}:
        raise ValueError("A auditoria não pode sobrescrever fontes.")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{result['repositories']} repositórios; {len(result['errors'])} erros; {result['status']}")
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
