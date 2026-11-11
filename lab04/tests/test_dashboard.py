"""Checagem automatizada do dashboard (Issue #79): importação, G1/G2 e app Streamlit."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from scipy.stats import binom

from lab04.src.captions import g1_caption, g2_caption
from lab04.src.data_adapter import get_real_outcomes
from lab04.src.plots import critical_k, critical_k_z, plot_g1, plot_g2
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_critical_k_matches_definition():
    k = critical_k(30, 0.05, 0.05)
    assert binom.sf(k - 1, 30, 0.05) < 0.05
    assert binom.sf(k - 2, 30, 0.05) >= 0.05


def test_critical_k_none_when_impossible():
    assert critical_k(2, 0.05, 0.001) is None


@pytest.mark.parametrize("n,alpha,z_threshold,exact_threshold", [
    (30, 0.05, 4, 5),
    (30, 0.01, 5, 6),
    (200, 0.05, 16, 16),
    (200, 0.01, 18, 19),
])
def test_g2_thresholds_are_consistent_with_one_sided_p_values(n, alpha, z_threshold, exact_threshold):
    assert critical_k_z(n, 0.05, alpha) == z_threshold
    assert critical_k(n, 0.05, alpha) == exact_threshold


def test_real_data_is_binary():
    data, provisional, source = get_real_outcomes()
    assert set(np.unique(data)).issubset({0, 1})
    assert provisional is False and source


@pytest.mark.parametrize("n,p", [(30, 0.10), (30, 0.0), (30, 1.0), (200, 0.05)])
def test_g1_g2_build_without_error(n, p):
    sim = simulate_runs(n, p, seed=42)
    reference = simulate_runs(200, p, seed=43)
    res = evaluate_tests(sim)
    real, _, _ = get_real_outcomes()
    g1 = plot_g1(real, sim, reference)
    assert len(g1.axes) == 3
    assert g1.axes[0].get_subplotspec().get_gridspec().get_geometry() == (3, 1)
    assert "n = 200" in g1.axes[2].get_title(loc="left")
    for ax, outcomes in zip(g1.axes, (real, sim, reference)):
        n, k = len(outcomes), outcomes.sum()
        assert ax.get_ylim() == (0, 1)
        assert [bar.get_height() for bar in ax.patches] == pytest.approx([(n - k) / n, k / n])
        assert [line.get_segments()[0][0, 1] for line in ax.collections] == pytest.approx([0.95, 0.05])
        assert f"{k}/{n}" in ax.texts[1].get_text()
    assert len(plot_g2(res).axes) == 2
    caption = g1_caption(
        len(real), int(real.sum()), n, int(sim.sum()),
        len(reference), int(reference.sum()), p, 0.05,
    )
    assert "200" in caption and "10.000 repetições oficiais" in caption
    assert "fronteira p = p₀" in g2_caption(res)


def test_g2_extreme_exploration_preserves_scale_and_marks_off_axis_observation():
    results = evaluate_tests(np.ones(1000), p0=0.01)
    binomial, normal = plot_g2(results).axes
    assert binomial.get_xlim()[1] < results["k"]
    assert normal.get_xlim() == (-4.0, 4.0)
    for ax in (binomial, normal):
        assert any(text.get_text() == "Observado →" for text in ax.texts)


def test_g2_legend_matches_the_two_tail_fills_and_the_rejection_markers():
    simulated = simulate_runs(30, 0.10, seed=42)
    fig = plot_g2(evaluate_tests(simulated))
    binomial, normal = fig.axes
    legend = fig.legends[0]
    orange, blue, rejection, observed, threshold = legend.legend_handles
    assert [entry.get_text() for entry in legend.get_texts()[:2]] == [
        "Cauda do p-valor · binomial", "Cauda do p-valor · Z"
    ]
    assert orange.get_facecolor() == pytest.approx(binomial.containers[1].patches[0].get_facecolor())
    assert blue.get_facecolor() == pytest.approx(normal.collections[0].get_facecolor()[0])
    assert rejection.get_hatch() == binomial.containers[2].patches[0].get_hatch()
    assert rejection.get_hatch() == normal.collections[1].get_hatch()
    assert observed.get_linestyle() == "-"
    assert threshold.get_linestyle() == "--"
    for ax in fig.axes:
        for key in (observed, threshold):
            assert any(line.get_color() == key.get_color() and line.get_linestyle() == key.get_linestyle()
                       for line in ax.lines)


def test_reference_sample_does_not_repeat_small_sample_prefix():
    small = simulate_runs(30, 0.1, seed=42)
    ref = simulate_runs(200, 0.1, seed=43)
    assert not np.array_equal(small, ref[:30])
    assert np.array_equal(ref, simulate_runs(200, 0.1, seed=43))


def test_streamlit_app_runs_without_exception():
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    text = " ".join(item.value for item in at.caption)
    assert "simulada" in text.lower() and "200" in text
