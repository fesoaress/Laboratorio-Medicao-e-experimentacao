"""Real CI results and final dashboard regression tests (Issue #85)."""

from pathlib import Path

import pytest
from scipy.stats import binomtest, norm

from lab04.src.real_data import load_ci_runs
from lab04.src.real_results import calculate_real_results, interpret_real_results

LAB04 = Path(__file__).resolve().parents[1]
CSV = LAB04 / "data" / "ci_runs.csv"


def test_observed_results_match_independent_statistical_calculation():
    result = calculate_real_results(load_ci_runs(CSV))
    assert (result["n"], result["k"]) == (169, 7)
    assert result["p_hat"] == pytest.approx(7 / 169)
    assert result["effect_pp"] == pytest.approx(100 * (7 / 169 - 0.05))
    assert result["effect_magnitude_pp"] == pytest.approx(abs(result["effect_pp"]))

    expected_z = (7 / 169 - 0.05) / (0.05 * 0.95 / 169) ** 0.5
    expected_exact = binomtest(7, 169, 0.05, alternative="greater").pvalue
    assert result["tests"]["z_statistic"] == pytest.approx(expected_z)
    assert result["tests"]["z_p_value"] == pytest.approx(norm.sf(expected_z))
    assert result["tests"]["binomial_p_value"] == pytest.approx(expected_exact)
    assert len(result["table_rows"]) == 2
    assert [r["statistic_name"] for r in result["table_rows"]] == ["Z", "K (falhas)"]
    assert [r["reject_h0"] for r in result["table_rows"]] == [False, False]
    assert "não comprova" in interpret_real_results(result)


def test_small_sample_can_make_the_tests_disagree():
    runs = load_ci_runs(CSV).head(30).copy()
    runs["failed"] = 0
    runs["conclusion"] = "success"
    runs.iloc[:4, runs.columns.get_loc("failed")] = 1
    runs.iloc[:4, runs.columns.get_loc("conclusion")] = "failure"
    result = calculate_real_results(runs)
    assert result["tests"]["reject_z"] is True
    assert result["tests"]["reject_binomial"] is False
    assert "decisões diferentes" in interpret_real_results(result)


@pytest.mark.parametrize("change,match", [
    ("duplicate", "Duplicate run_id"),
    ("cancelled", "Only completed"),
    ("wrong_indicator", "indicator disagrees"),
])
def test_invalid_real_rows_are_rejected(change, match):
    runs = load_ci_runs(CSV).copy()
    if change == "duplicate":
        runs.loc[1, "run_id"] = runs.loc[0, "run_id"]
    elif change == "cancelled":
        runs.loc[0, "conclusion"] = "cancelled"
    else:
        runs.loc[0, "failed"] = 1 - runs.loc[0, "failed"]
    with pytest.raises(ValueError, match=match):
        calculate_real_results(runs)


@pytest.mark.parametrize("p0,alpha", [(0, 0.05), (0.05, 0), (1, 0.05)])
def test_invalid_test_parameters_are_rejected(p0, alpha):
    with pytest.raises(ValueError):
        calculate_real_results(load_ci_runs(CSV), p0=p0, alpha=alpha)


def test_final_dashboard_sections_use_the_real_results(monkeypatch):
    pytest.importorskip("streamlit")
    from lab04 import app

    class Recorder:
        def __init__(self):
            self.headers, self.tables, self.texts, self.warnings = [], [], [], []

        def header(self, value, **_kwargs):
            self.headers.append(value)

        def dataframe(self, value, **_kwargs):
            self.tables.append(value)

        def caption(self, value):
            self.texts.append(value)

        def markdown(self, value):
            self.texts.append(value)

        def warning(self, value):
            self.warnings.append(value)

        def info(self, value):
            self.texts.append(value)

    recorder = Recorder()
    monkeypatch.setattr(app, "st", recorder)

    ctx = app.build_context(n=30, true_p=0.10, seed=42, p0=0.05, alpha=0.05)
    app.section_dados_reais(ctx)
    app.section_conclusao(ctx)

    assert recorder.headers == ["6. Dados reais", "7. Conclusão"]
    assert len(recorder.tables) == 1
    table = recorder.tables[0]
    assert len(table) == 2
    assert list(table["Conclusão"]) == ["Não rejeita H₀", "Não rejeita H₀"]
    assert list(table["Efeito p̂−p₀ (p.p.)"]) == ["-0,86", "-0,86"]
    assert not recorder.warnings
