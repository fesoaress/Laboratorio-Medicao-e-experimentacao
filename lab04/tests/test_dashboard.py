"""Checagem automatizada do dashboard (Issue #79): importação, G1/G2 e app Streamlit."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pytest
from scipy.stats import binom

from lab04.src.captions import g1_caption, g2_caption
from lab04.src.data_adapter import get_real_outcomes
from lab04.src.plots import critical_k, plot_g1, plot_g2
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests

APP = Path(__file__).resolve().parents[1] / "app.py"


def test_critical_k_matches_definition():
    k = critical_k(30, 0.05, 0.05)
    assert binom.sf(k - 1, 30, 0.05) < 0.05
    assert binom.sf(k - 2, 30, 0.05) >= 0.05


def test_critical_k_none_when_impossible():
    assert critical_k(2, 0.05, 0.001) is None


def test_real_data_is_binary():
    data, provisional, source = get_real_outcomes()
    assert set(np.unique(data)).issubset({0, 1})
    assert provisional is False and source


@pytest.mark.parametrize("n,p", [(30, 0.10), (30, 0.0), (30, 1.0), (200, 0.05)])
def test_g1_g2_build_without_error(n, p):
    sim = simulate_runs(n, p, seed=42)
    res = evaluate_tests(sim)
    real, _, _ = get_real_outcomes()
    g1 = plot_g1(real, sim)
    assert len(g1.axes) == 2
    for ax, outcomes in zip(g1.axes, (real, sim)):
        n, k = len(outcomes), outcomes.sum()
        assert ax.get_ylim() == (0, 1)
        assert [bar.get_height() for bar in ax.patches] == pytest.approx([(n - k) / n, k / n])
        assert [line.get_segments()[0][0, 1] for line in ax.collections] == pytest.approx([0.95, 0.05])
        assert f"{k}/{n}" in ax.texts[1].get_text()
    assert len(plot_g2(res).axes) == 2
    assert g1_caption(len(real), int(real.sum()), n, int(sim.sum()), 0.05)
    assert "fronteira p = p₀" in g2_caption(res)


def test_g2_extreme_exploration_preserves_scale_and_marks_off_axis_observation():
    results = evaluate_tests(np.ones(1000), p0=0.01)
    binomial, normal = plot_g2(results).axes
    assert binomial.get_xlim()[1] < results["k"]
    assert normal.get_xlim() == (-4.0, 4.0)
    for ax in (binomial, normal):
        assert any(text.get_text() == "Observado →" for text in ax.texts)


def test_streamlit_app_runs_without_exception():
    testing = pytest.importorskip("streamlit.testing.v1")
    at = testing.AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
