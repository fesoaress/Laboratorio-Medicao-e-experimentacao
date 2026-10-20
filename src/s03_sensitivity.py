"""RQ07 combinações originais; RQ08 distingue retrabalho de CFR(b) (#66, #68)."""

import gzip
import json
from collections import Counter, defaultdict
from itertools import combinations

import numpy as np
import pandas as pd
from sklearn.metrics import cohen_kappa_score

from .cfr_delivery import calculate
from .corrective import predict
from .gold_sample import timestamp
from .s03_descriptive import CATEGORIES, category, general
from .temporal import ObservationWindow


def lead_time(events, contexts):
    values, statuses = [], Counter()
    problems = []
    for event in events:
        key = event["pair_key"]
        context = contexts.get(key, {})
        status = context.get("status", "no_previous_release" if not key else "missing")
        statuses[status] += 1
        if status in ("no_previous_release", "ignored_compare_404"):
            continue
        if status != "complete":
            problems.append(f"{event['identifier']}:{status}")
            continue
        commits = {c["sha"]: c for c in context["commits"]}
        durations = [(timestamp(event["date"]) - timestamp(c["author_date"])).total_seconds() / 3600 for c in commits.values()]
        if any(v < 0 for v in durations):
            problems.append(f"{event['identifier']}:negative_author_lead_time")
        values.extend(durations)
    valid = bool(values) and not problems
    return {"lead_time_hours": float(np.median(values)) if valid else None,
            "observations": len(values), "status": "calculated" if valid else "incomplete_or_negative" if problems else "no_commit_observations",
            "interval_statuses": json.dumps(dict(statuses), sort_keys=True), "errors": "|".join(problems)}


def classify_c2(events, contexts):
    predictions = []
    for event in events:
        context = contexts.get(event["pair_key"], {})
        status = context.get("status", "no_previous_release" if not event["pair_key"] else "missing")
        result = predict(tag=event["tag_name"], previous_tag=context.get("base_tag", ""), body=event["body"],
            messages=[c["message"] for c in context.get("commits", [])], interval_status=status, version="v5")
        usable = result.correction_notes + result.feature_notes > 0 or status == "complete"
        predictions.append({"full_name": event["full_name"], "release_id": event["identifier"],
            "tag_name": event["tag_name"], "published_at": event["date"], "previous_release_id": event["previous_identifier"],
            "prerelease": event["prerelease"], "classification_usable": usable,
            "pair_key": event["pair_key"], **result.to_dict()})
    return predictions


def pair_compare(left, right):
    if len(left) != len(right):
        raise ValueError("Classificações pareadas precisam ter o mesmo comprimento.")
    valid = [(a, b) for a, b in zip(left, right) if pd.notna(a) and pd.notna(b)]
    result = dict(n=len(valid), changed=None, percent_changed=None, kappa_linear=None, status="no_paired_data")
    if not valid:
        return result
    a, b = zip(*valid)
    changed = sum(x != y for x, y in valid)
    result.update(changed=changed, percent_changed=changed * 100 / len(valid))
    if len(set(a) | set(b)) == 1:
        result["status"] = "undefined_constant"
    else:
        result.update(kappa_linear=float(cohen_kappa_score(a, b, labels=list(CATEGORIES), weights="linear")), status="calculated")
    return result


def compare_classifications(classes):
    rows = []
    for left, right in combinations(("C1", "C2", "C3"), 2):
        for metric in ("df", "lt", "cfr", "recovery", "general"):
            rows.append({"left": left, "right": right, "metric": metric,
                         **pair_compare(classes[f"{left}_{metric}"], classes[f"{right}_{metric}"])})
    return pd.DataFrame(rows)


def run(data, base_classes, folder):
    with gzip.open(folder / "variant_plan.json.gz", "rt", encoding="utf-8") as handle:
        specification = json.load(handle)
    contexts = {}
    for part in sorted((folder / "variant_context").glob("part-*.jsonl.gz")):
        with gzip.open(part, "rt", encoding="utf-8") as handle:
            for line in handle:
                context = json.loads(line)
                if context["pair_key"] in contexts:
                    raise ValueError("Contexto de comparação duplicado.")
                contexts[context["pair_key"]] = context
    if set(contexts) != set(specification["pairs"]):
        raise ValueError("Snapshot de comparações incompleto.")
    window = ObservationWindow(**specification["window"])
    days = (window.end - window.start).days
    grouped = defaultdict(list)
    for event in specification["events"]:
        if not window.contains(event["date"]):
            raise ValueError("Evento da variante fora da janela.")
        grouped[event["variant"], event["full_name"]].append(event)
    predictions = classify_c2([e for e in specification["events"] if e["variant"] == "C2"], contexts)
    cb, details = calculate(predictions, window)
    cfr = {r["full_name"]: r for r in cb}
    metrics = []
    classes = data[["full_name"]].copy()
    for metric, key in (("df", "df"), ("lt", "lt_release"), ("cfr", "cfr_a"), ("recovery", "recovery"), ("general", "general")):
        classes[f"C1_{metric}"] = base_classes[key].to_list()
    for variant in ("C2", "C3"):
        for metric in ("df", "lt", "cfr", "recovery", "general"):
            classes[f"{variant}_{metric}"] = pd.Series([None] * len(data), dtype=object)
        for index, repository in data.iterrows():
            name = repository.full_name
            events = grouped[variant, name]
            lead = lead_time(events, contexts)
            frequency = len(events) * 7 / days
            failure = (cfr.get(name, {}).get("cfr_delivery") if variant == "C2" else repository.cfr_ci)
            failure = None if failure in (None, "") else float(failure)
            scores = [category("df", frequency, len(events) * 30 / days), category("lt_commit", lead["lead_time_hours"]),
                      category("cfr_b" if variant == "C2" else "cfr_a", failure), category("recovery", repository.recovery_time_median_hours)]
            for key, value in zip(("df", "lt", "cfr", "recovery", "general"), [*scores, general(scores)]):
                classes.loc[index, f"{variant}_{key}"] = value
            metrics.append({"variant": variant, "full_name": name, "events": len(events), "df_per_week": frequency,
                            "cfr": failure, "recovery_hours": repository.recovery_time_median_hours, **lead})
    provenance = pd.DataFrame([{"pair_key": key, **{k: c.get(k, "") for k in ("full_name", "base", "head", "base_tag", "head_tag", "base_date", "head_date", "source", "source_release_id", "transport", "url", "status", "error", "error_status")},
                                "commits": len(c["commits"])} for key, c in contexts.items()])
    return pd.DataFrame(metrics), classes, compare_classifications(classes), pd.DataFrame(predictions), pd.DataFrame(details), provenance


def rework(predictions):
    grouped = defaultdict(list)
    for row in predictions:
        grouped[row["full_name"]].append(row)
    rows = []
    for name, pool in sorted(grouped.items()):
        unknown = sum(str(r["classification_usable"]).lower() == "false" for r in pool)
        positive = sum(str(r["classification_usable"]).lower() == "true" and r["corrective_release"] == "yes" for r in pool)
        total = len(pool)
        rows.append({"full_name": name, "total_stable_releases": total, "known_corrective": positive, "unknown": unknown,
            "rework_rate": positive / total if not unknown else None, "lower_bound": positive / total,
            "upper_bound": (positive + unknown) / total, "status": "calculated" if not unknown else "incomplete_classification"})
    return pd.DataFrame(rows)
