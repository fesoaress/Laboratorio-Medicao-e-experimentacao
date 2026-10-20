import gzip
import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src import s03, s03_sensitivity
from src.s03_collect import save
from src.s03_descriptive import METRICS, classify


def synthetic_data():
    rows = []
    for i in range(24):
        row = {field: float(i + 1) for field, _, _ in METRICS.values()}
        row.update(full_name=f"o/r{i}", deployment_frequency_per_month=float(i + 1), cfr_ci=i/24, cfr_delivery=(23-i)/24,
                   stargazers_count=i + 1, contributors_count=i + 1, repo_age_days=i + 1)
        rows.append(row)
    rows[-1]["deployment_frequency_per_week"] = 10000
    return pd.DataFrame(rows)


def variant_fixture(folder, data):
    events, contexts = [], []
    for name in data.full_name:
        for variant in ("C2", "C3"):
            key = name + variant
            events.append(dict(full_name=name, identifier="1", variant=variant, pair_key=key,
                previous_identifier="0", tag_name="v1", date="2026-01-02T00:00:00Z", body="fix: crash", prerelease="False"))
            contexts.append(dict(pair_key=key, full_name=name, status="complete", source="complementary", base_tag="v0",
                commits=[dict(sha="sha", author_date="2026-01-01T00:00:00Z", message="fix: crash")]))
    with gzip.open(folder / "variant_plan.json.gz", "wt", encoding="utf-8") as handle:
        json.dump(dict(window=dict(start_date="2025-10-01", end_date="2026-10-01"), events=events,
                       pairs={r["pair_key"]: {} for r in contexts}), handle)
    (folder / "variant_context").mkdir()
    with gzip.open(folder / "variant_context/part-000.jsonl.gz", "wt", encoding="utf-8") as handle:
        for context in contexts:
            handle.write(json.dumps(context) + "\n")


def test_full_offline_pipeline_produces_inspectable_outputs(tmp_path, monkeypatch):
    data = synthetic_data()
    output, reports, figures = (tmp_path / n for n in ("data", "reports", "figures"))
    output.mkdir()
    variant_fixture(output, data)
    monkeypatch.setattr(s03.s03_audit, "run", lambda: dict(protected_sources=[]))
    monkeypatch.setattr(s03.s03_descriptive, "load_data", lambda p: data)
    monkeypatch.setattr(s03, "read_csv", lambda p: [dict(full_name="o/r0", classification_usable="True", corrective_release="yes")])
    result = s03.run(output, reports, figures, permutations=19, iterations=1000)
    assert result["status"] == "analyses_executed"
    comparison = pd.read_csv(output / "sensitivity.csv")
    assert len(comparison) == 15 and comparison.n.max() == 24
    assert len(list(figures.glob("*.png"))) == 9
    assert len(list(figures.glob("*.svg"))) == 9
    assert len(list(figures.glob("*.pdf"))) == 9
    assert (reports / "manifest.json").exists()
    monkeypatch.setattr(s03.s03_figures, "run", lambda *a: None)
    result = s03.run(output, reports, figures, core_only=True, permutations=19, iterations=1000)
    assert result["status"] == "core_complete_rq07_pending"


def test_variants_reject_outside_window(tmp_path):
    data = synthetic_data()
    variant_fixture(tmp_path, data)
    path = tmp_path / "variant_plan.json.gz"
    with gzip.open(path, "rt", encoding="utf-8") as handle:
        plan = json.load(handle)
    plan["events"][0]["date"] = "2026-10-01T00:00:00Z"
    with gzip.open(path, "wt", encoding="utf-8") as handle:
        json.dump(plan, handle)
    with pytest.raises(ValueError, match="fora da janela"):
        s03_sensitivity.run(data, classify(data), tmp_path)


def test_pipeline_cli(monkeypatch):
    seen = []
    monkeypatch.setattr(s03, "run", lambda *a, **kw: seen.append(kw))
    assert s03.main(["--core-only"]) == 0
    assert seen[0]["core_only"] is True
