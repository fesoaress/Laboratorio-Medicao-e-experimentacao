"""Testes de G3/G4 (Issue #83): leitura das tabelas, renderização e correspondência com os dados."""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import numpy as np
import pandas as pd
import pytest

from lab04.src.captions import g3_caption, g4_caption
from lab04.src.plots import COLOR_BINOMIAL, COLOR_Z, plot_g3, plot_g4
from lab04.src.s02_results import (
    REQUIRED_COLUMNS, classify_type1, combine_conditions, load_s02_tables,
    power_table, type1_table, validate_s02_table,
)

APP = Path(__file__).resolve().parents[1] / "app.py"
REPS = 10_000
P_VALUES = [0.05, 0.075, 0.10, 0.125, 0.15, 0.20]


def make_table(n, z_counts, b_counts, p0=0.05, alpha=0.05, seed=42):
    """Fixture controlada (valores escolhidos à mão, não produzidos por simulação)."""
    rows = []
    for p, zc, bc in zip(P_VALUES, z_counts, b_counts):
        zr, br = zc / REPS, bc / REPS
        rows.append({
            "n": n, "p0": p0, "alpha": alpha, "seed": seed, "p_true": p,
            "effect_pp": round(100 * (p - p0), 10), "repetitions": REPS,
            "z_rejections": zc, "binomial_rejections": bc,
            "z_rejection_rate": zr, "binomial_rejection_rate": br,
            "z_monte_carlo_se": (zr * (1 - zr) / REPS) ** 0.5,
            "binomial_monte_carlo_se": (br * (1 - br) / REPS) ** 0.5,
        })
    return pd.DataFrame(rows)


@pytest.fixture
def ref():
    return make_table(200, [520, 2400, 6100, 8500, 9500, 9990], [380, 2000, 5600, 8200, 9400, 9985])


@pytest.fixture
def q3():
    return make_table(30, [60, 900, 2500, 4300, 6100, 8600], [250, 1200, 2700, 4400, 6000, 8300])


@pytest.fixture
def cond(ref, q3):
    return combine_conditions([validate_s02_table(ref, "ref"), validate_s02_table(q3, "q3")])


def test_validate_accepts_fixture_and_sorts(ref):
    out = validate_s02_table(ref.iloc[::-1], "ref")
    assert list(out["effect_pp"]) == sorted(out["effect_pp"])
    assert set(REQUIRED_COLUMNS) <= set(out.columns)


def test_validate_rejects_missing_column_and_inconsistent_rate(ref):
    with pytest.raises(ValueError, match="colunas ausentes"):
        validate_s02_table(ref.drop(columns=["z_rejections"]))
    bad = ref.copy()
    bad.loc[1, "z_rejection_rate"] = 0.9
    with pytest.raises(ValueError, match="não confere"):
        validate_s02_table(bad)


def test_validate_requires_zero_effect(ref):
    with pytest.raises(ValueError, match="efeito zero"):
        validate_s02_table(ref.iloc[1:])


def test_combine_labels_conditions_from_parameters(cond):
    labels = list(cond["condition"].cat.categories)
    assert labels == ["n = 200 (n·p0 = 10)", "n = 30 (n·p0 = 1,5)"]
    assert cond.loc[cond["n"] == 30, "normal_ok"].eq(False).all()
    assert cond.loc[cond["n"] == 200, "normal_ok"].eq(True).all()


def test_classify_type1():
    assert classify_type1(0.052, 0.05, REPS) == "compatível com α"
    assert classify_type1(0.07, 0.05, REPS) == "liberal"
    assert classify_type1(0.02, 0.05, REPS) == "conservador"


def test_g3_bars_match_aggregated_table(cond):
    t1 = type1_table(cond)
    fig = plot_g3(t1)
    ax = fig.axes[0]
    bar_sets = [c for c in ax.containers if isinstance(c, matplotlib.container.BarContainer)]
    z_bars, b_bars = bar_sets
    assert [b.get_height() for b in z_bars] == pytest.approx(list(t1["z_rate"]))
    assert [b.get_height() for b in b_bars] == pytest.approx(list(t1["binomial_rate"]))
    assert z_bars[0].get_facecolor()[:3] == pytest.approx(matplotlib.colors.to_rgb(COLOR_Z))
    assert b_bars[0].get_facecolor()[:3] == pytest.approx(matplotlib.colors.to_rgb(COLOR_BINOMIAL))
    hlines = [ln.get_ydata()[0] for ln in ax.lines]
    assert 0.05 in hlines
    assert ax.get_xlabel() and ax.get_ylabel() and ax.get_title()


def test_g3_values_come_from_zero_effect_rows(cond, ref):
    t1 = type1_table(cond)
    row = t1[t1["n"] == 200].iloc[0]
    assert row["z_rate"] == ref.loc[0, "z_rejection_rate"]
    assert row["z_status"] == "compatível com α"
    small = t1[t1["n"] == 30].iloc[0]
    assert small["z_status"] == "conservador"
    assert small["binomial_status"] == "conservador"


def test_g4_lines_match_aggregated_table_and_start_at_zero(cond):
    pw = power_table(cond)
    fig = plot_g4(pw)
    ax = fig.axes[0]
    curves = [ln for ln in ax.lines if len(ln.get_xdata()) == len(P_VALUES)]
    assert len(curves) == 4  # 2 testes × 2 condições
    for ln in curves:
        assert ln.get_xdata()[0] == 0
        color = matplotlib.colors.to_hex(ln.get_color())
        assert color in (COLOR_Z, COLOR_BINOMIAL)
        for cname, g in pw.groupby("condition", sort=False):
            col = "z_rate" if color == COLOR_Z else "binomial_rate"
            if np.allclose(ln.get_ydata(), g[col].to_numpy()):
                break
        else:
            pytest.fail("curva sem correspondência nos dados agregados")
    assert ax.get_xlim()[0] == 0


def test_captions_are_neutral_and_mention_simulation(cond):
    t1, pw = type1_table(cond), power_table(cond)
    c3, c4 = g3_caption(t1), g4_caption(pw, 0.05)
    assert "simulados" in c3 and "5,00%" in c3 and "10.000" in c3
    assert "10.000" in c4 and "venc" not in (c3 + c4).lower() and "melhor" not in (c3 + c4).lower()


def test_load_tables_handles_missing_files(tmp_path, ref):
    assert load_s02_tables(tmp_path) == {"q1_q2": None, "q3": None}
    ref.to_csv(tmp_path / "s02_q1_q2.csv", index=False)
    tables = load_s02_tables(tmp_path)
    assert tables["q3"] is None and len(tables["q1_q2"]) == 6


def test_app_renders_g3_g4_with_fixture_and_g1_g2_still_present(tmp_path, monkeypatch, ref, q3):
    testing = pytest.importorskip("streamlit.testing.v1")
    ref.to_csv(tmp_path / "s02_q1_q2.csv", index=False)
    q3.to_csv(tmp_path / "s02_q3.csv", index=False)
    monkeypatch.setenv("LAB04_RESULTS_DIR", str(tmp_path))
    at = testing.AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    headers = [h.value for h in at.header]
    assert "2. Os dados (G1)" in headers and "3. Como os testes funcionam (G2)" in headers
    assert "4. Erro tipo I (G3)" in headers and "5. Poder (G4)" in headers
    assert not at.info and not at.error


def test_app_shows_notice_when_tables_absent(tmp_path, monkeypatch):
    testing = pytest.importorskip("streamlit.testing.v1")
    monkeypatch.setenv("LAB04_RESULTS_DIR", str(tmp_path))
    at = testing.AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("não encontradas" in i.value for i in at.info)


def test_app_reports_invalid_table(tmp_path, monkeypatch, ref):
    testing = pytest.importorskip("streamlit.testing.v1")
    ref.drop(columns=["z_rejections"]).to_csv(tmp_path / "s02_q1_q2.csv", index=False)
    monkeypatch.setenv("LAB04_RESULTS_DIR", str(tmp_path))
    at = testing.AppTest.from_file(str(APP), default_timeout=60).run()
    assert not at.exception
    assert any("colunas ausentes" in e.value for e in at.error)