"""Conferências independentes dos artefatos empíricos; sem novas consultas."""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from src.gold_sample import read_csv, sha256, timestamp
from src.s03_audit import independent_cfr


def test_rq07_contingency_formula_reconciles_real_results():
    folder = Path("data/processed/s03")
    classes = pd.read_csv(folder / "variant_classifications.csv")
    order = {value: i for i, value in enumerate(("Low", "Medium", "High", "Elite"))}
    weights = np.abs(np.subtract.outer(np.arange(4), np.arange(4)))
    for row in pd.read_csv(folder / "sensitivity.csv").itertuples(index=False):
        pairs = classes[[f"{row.left}_{row.metric}", f"{row.right}_{row.metric}"]].dropna()
        table = np.zeros((4, 4))
        for a, b in pairs.itertuples(index=False, name=None):
            table[order[a], order[b]] += 1
        total = table.sum()
        expected = np.outer(table.sum(axis=1), table.sum(axis=0)) / total
        kappa = 1 - (weights * table).sum() / (weights * expected).sum()
        assert row.n == total
        assert row.changed == total - np.trace(table)
        assert row.percent_changed == pytest.approx(row.changed / total * 100)
        assert row.kappa_linear == pytest.approx(kappa)


def test_real_c2_cfr_has_correct_censoring_and_no_stable_substitution():
    folder = Path("data/processed/s03")
    predictions = read_csv(folder / "c2_predictions.csv")
    details = read_csv(folder / "c2_cfr_events.csv")
    assert len(predictions) == 29007
    assert sum(r["prerelease"] == "True" for r in predictions) == 1855
    statuses = independent_cfr(predictions, details, timestamp("2026-10-01T00:00:00Z").timestamp())
    assert statuses == dict(failed=21531, not_failed=6657, right_censored=784, unassessable_context=35)
    assert sum(statuses.values()) == len(predictions)


def test_versioned_manifest_matches_real_input_output_bytes():
    manifest = json.loads(Path("reports/s03/manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "analyses_executed"
    assert manifest["repositories"] == 311 and manifest["seed"] == 42
    for source in [*manifest["sources"], *manifest["outputs"], *manifest["figures"]]:
        assert sha256(Path(source["path"])) == source["sha256"], source["path"]


def test_rework_and_cfr_count_different_units():
    folder = Path("data/processed/s03")
    rework = pd.read_csv(folder / "rework.csv")
    assert rework.rework_rate.notna().sum() == 274
    assert rework.rework_rate.isna().sum() == 37
    assert rework.unknown.sum() == 180
    assert (rework.lower_bound <= rework.upper_bound).all()
    assert (rework.loc[rework.unknown == 0, "lower_bound"] == rework.loc[rework.unknown == 0, "upper_bound"]).all()
