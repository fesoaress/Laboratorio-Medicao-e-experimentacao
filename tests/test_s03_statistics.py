import numpy as np
import pandas as pd
import pytest
import gzip
import json
from scipy import stats

from src import s03_bootstrap as b, s03_descriptive as d, s03_inference as inf
from src import s03_sensitivity as sens


@pytest.mark.parametrize("metric,value,monthly,expected", [
    ("df", 7, 30, "Elite"), ("df", 1, 4.3, "High"), ("df", 7/30, 1, "Medium"), ("df", .1, .9, "Low"),
    ("lt_release", 23.99, None, "Elite"), ("lt_commit", 24, None, "High"), ("lt_release", 168, None, "Medium"), ("lt_commit", 720, None, "Low"),
    ("cfr_a", .15, None, "Elite"), ("cfr_b", .30, None, "High"), ("cfr_a", .45, None, "Medium"), ("cfr_b", .45001, None, "Low"),
    ("recovery", .999, None, "Elite"), ("recovery", 1, None, "High"), ("recovery", 24, None, "Medium"), ("recovery", 168, None, "Low"),
    ("recovery", np.nan, None, None), ("cfr_a", None, None, None)])
def test_dora_boundaries(metric, value, monthly, expected):
    assert d.category(metric, value, monthly) == expected


@pytest.mark.parametrize("metric,value,monthly", [("df", 1, None), ("df", 1, -1), ("recovery", -1, None),
    ("cfr_a", 1.01, None), ("unknown", 1, None), ("lt_release", np.inf, None)])
def test_dora_rejects_invalid(metric, value, monthly):
    with pytest.raises(ValueError):
        d.category(metric, value, monthly)


def test_general_floor_and_missing():
    assert d.general(["Elite", "High", "Medium", "Low"]) == "Medium"
    assert d.general(["Elite", "Elite", "Elite", None]) is None
    with pytest.raises(ValueError):
        d.general(["Elite"])


def test_describe_type7_and_missing():
    result = d.describe([0, 1, 2, 3, np.nan])
    assert result == dict(n=4, missing=1, median=1.5, q1=.75, q3=2.25, iqr=1.5, minimum=0, maximum=3)
    assert d.describe([np.nan])["median"] is None


def test_load_validates_domains(tmp_path):
    row = {field: 1 for field, _, _ in d.METRICS.values()}
    row.update(full_name="o/r", deployment_frequency_per_month=1, stargazers_count=1, contributors_count=1, repo_age_days=1)
    path = tmp_path / "data.csv"
    pd.DataFrame([row]).to_csv(path, index=False)
    assert len(d.load_data(path)) == 1
    for update in ({"cfr_ci": 1.5}, {"cfr_ci": -1}, {"contributors_count": np.inf}):
        pd.DataFrame([{**row, **update}]).to_csv(path, index=False)
        with pytest.raises(ValueError):
            d.load_data(path)
    pd.DataFrame([row, row]).to_csv(path, index=False)
    with pytest.raises(ValueError):
        d.load_data(path)


def test_spearman_ties_missing_permutation_reproducible():
    x, y = [1, 2, 2, 4, np.nan], [4, 1, 1, 0, 8]
    a = inf.spearman(x, y, 99)
    assert a == inf.spearman(x, y, 99)
    assert a["n"] == 4 and a["rho"] == pytest.approx(-1)
    assert a["rho"] == pytest.approx(stats.spearmanr(x[:4], y[:4]).statistic)
    assert inf.spearman([1, 1, 1], [1, 2, 3])["rho"] is None
    assert inf.spearman([1], [2])["status"] == "insufficient_or_constant"


def test_holm_family_and_undefined():
    rows = [dict(p=.01), dict(p=.04), dict(p=None), dict(p=.03)]
    assert [r["p_holm"] for r in inf.holm(rows)] == [.03, .06, None, .06]
    assert inf.holm([dict(p=None)])[0]["p_holm"] is None


def test_quartiles_do_not_split_ties():
    labels, cuts = inf.groups_for([1, 1, 1, 1, 2, 3, 4, np.nan])
    assert len(set(labels[:4])) == 1 and labels[-1] == -1
    assert np.all(np.diff(cuts) > 0)
    labels, cuts = inf.groups_for([np.nan])
    assert not len(cuts) and labels[0] == -1


def test_group_tests_and_effects():
    groups = [np.arange(i, i + 8) for i in (0, 10, 20)]
    result = inf.compare_groups(groups)
    expected = stats.kruskal(*groups)
    assert result["statistic"] == expected.statistic
    assert result["effect"] == expected.statistic / 23
    assert inf.compare_groups([[1, 2], [3, 4]])["effect"] == -1
    assert inf.compare_groups([[1], [2], [3]])["status"] == "insufficient_group_size_min5"
    assert inf.compare_groups([[1] * 5] * 3)["status"] == "constant"
    assert inf.compare_groups([[], [np.nan], [2]])["p"] is None


def test_bootstrap_preserves_pairs_and_repeats():
    a = b.bootstrap([1, 2, 3, 4], iterations=1000)
    assert a == b.bootstrap([1, 2, 3, 4], iterations=1000)
    assert a["estimate"] == 2.5 and a["lower95"] <= 2.5 <= a["upper95"]
    pair = b.bootstrap(np.arange(10), -np.arange(10), iterations=1000)
    assert pair["lower95"] == pytest.approx(-1)
    assert pair["upper95"] == pytest.approx(-1)
    assert b.bootstrap([1, 1, 1], [2, 3, 4], iterations=1000)["status"] == "constant"
    assert b.bootstrap([np.nan], iterations=1000)["status"] == "insufficient"
    with pytest.raises(ValueError):
        b.bootstrap([1, 2], iterations=999)


def test_paired_kappa_uses_order_and_valid_pairs():
    result = sens.pair_compare(["Low", "Medium", "High", "Elite", None], ["Medium", "Medium", "Elite", "Elite", "Low"])
    # Observed mean ordinal distance=.5; expected from independent marginals=1.25.
    assert result["n"] == 4 and result["percent_changed"] == 50
    assert result["kappa_linear"] == pytest.approx(1 - .5 / 1.25)
    assert sens.pair_compare([None], ["Low"])["n"] == 0
    assert sens.pair_compare(["High"], ["High"])["status"] == "undefined_constant"
    with pytest.raises(ValueError):
        sens.pair_compare([], ["Low"])


def event(key="k", date="2026-01-02T00:00:00Z"):
    return dict(pair_key=key, identifier="1", date=date, full_name="o/r", tag_name="v1", body="fix: crash", previous_identifier="", prerelease="False")

def test_sensitivity_rejects_incomplete_context(tmp_path):
    folder = tmp_path
    specification = {"window": {"start_date": "2025-01-01", "end_date": "2026-01-01"}, "repositories": [], "events": [], "pairs": {"key1": {}}}
    with gzip.open(folder / "variant_plan.json.gz", "wt", encoding="utf-8") as f:
        json.dump(specification, f)
    (folder / "variant_context").mkdir()
    with gzip.open(folder / "variant_context/part-000.jsonl.gz", "wt", encoding="utf-8") as f:
        f.write(json.dumps({"pair_key": "key2"}) + "\n")
    
    data = pd.DataFrame({"full_name": ["o/r"]})
    base_classes = pd.DataFrame({"df": [1], "lt_release": [1], "cfr_a": [1], "recovery": [1], "general": ["Low"]})
    
    with pytest.raises(ValueError, match="Snapshot de comparações incompleto."):
        sens.run(data, base_classes, folder)

def test_variant_lead_time_not_stable_substitution():
    context = {"k": {"status": "complete", "commits": [dict(sha="a", author_date="2026-01-01T00:00:00Z", message="fix: crash")]}}
    assert sens.lead_time([event()], context)["lead_time_hours"] == 24
    assert sens.lead_time([event(date="2025-01-01T00:00:00Z")], context)["lead_time_hours"] is None
    assert sens.lead_time([event()], {})["lead_time_hours"] is None
    assert sens.lead_time([event(key="")], {})["status"] == "no_commit_observations"
    context["k"]["status"] = "ignored_compare_404"
    assert sens.lead_time([event()], context)["lead_time_hours"] is None
    prediction = sens.classify_c2([event()], context)[0]
    assert prediction["classification_usable"] is True  # Notes suffice under accepted v5.
    empty = event()
    empty["body"] = ""
    assert sens.classify_c2([empty], context)[0]["classification_usable"] is False


def test_rework_unknown_is_not_negative():
    rows = [dict(full_name="o/r", classification_usable="True", corrective_release="yes"),
            dict(full_name="o/r", classification_usable="False", corrective_release="no")]
    result = sens.rework(rows).iloc[0]
    assert pd.isna(result.rework_rate) and result.lower_bound == .5 and result.upper_bound == 1
    assert sens.rework(rows[:1]).iloc[0].rework_rate == 1
