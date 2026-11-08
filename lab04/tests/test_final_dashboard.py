"""Smoke test da entrega final (Issue #84): ordem das 7 seções, textos, dados reais e achados."""

import math
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")

import pandas as pd
import pytest

from lab04.src.conclusion import power_direction, power_sentence
from lab04.src.real_summary import cohens_h, effect_summary, effect_text

sys.path.insert(0, str(Path(__file__).parent))
from test_s02_plots import make_table  # noqa: E402  (fixture controlada da #83)

APP = Path(__file__).resolve().parents[1] / "app.py"
DATA_DIR = Path(__file__).resolve().parents[1] / "data"
SECTION_ORDER = [
    "1. Cenário", "2. Os dados (G1)", "3. Como os testes funcionam (G2)", "4. Erro tipo I (G3)",
    "5. Poder (G4)", "6. Dados reais", "7. Conclusão",
]


@pytest.fixture
def results_dir(tmp_path, monkeypatch):
    make_table(200, [520, 2400, 6100, 8500, 9500, 9990], [380, 2000, 5600, 8200, 9400, 9985]).to_csv(
        tmp_path / "s02_q1_q2.csv", index=False)
    make_table(30, [60, 900, 2500, 4300, 6100, 8600], [250, 1200, 2700, 4400, 6000, 8300]).to_csv(
        tmp_path / "s02_q3.csv", index=False)
    monkeypatch.setenv("LAB04_RESULTS_DIR", str(tmp_path))
    return tmp_path


def run_app():
    testing = pytest.importorskip("streamlit.testing.v1")
    return testing.AppTest.from_file(str(APP), default_timeout=90).run()


def test_sections_follow_assignment_order(results_dir):
    at = run_app()
    assert not at.exception
    assert [h.value for h in at.main.header] == SECTION_ORDER


def test_each_chart_section_has_caption_and_no_provisional_marker(results_dir):
    at = run_app()
    captions = " ".join(c.value for c in at.caption)
    for expected in ("histogramas", "p-valor", "repetições simuladas", "Hipóteses e α"):
        assert expected in captions
    page = " ".join(m.value for m in at.markdown) + captions
    assert "PROVISÓRI" not in page.upper()


def test_no_provisional_data_file_in_delivery():
    assert not (DATA_DIR / "provisional_ci_runs.csv").exists()


def test_effect_summary_formulas():
    eff = effect_summary(7, 169, 0.05)
    assert eff["p_hat"] == pytest.approx(7 / 169)
    assert eff["diff_pp"] == pytest.approx(100 * (7 / 169 - 0.05))
    assert eff["h"] == pytest.approx(2 * math.asin(math.sqrt(7 / 169)) - 2 * math.asin(math.sqrt(0.05)))
    assert eff["ci_low"] < 7 / 169 < eff["ci_high"]
    assert cohens_h(0.1, 0.1) == 0


def test_effect_text_mentions_effect_size_and_interval():
    text = effect_text(effect_summary(7, 169, 0.05))
    assert "h de Cohen" in text and "intervalo exato de 95%" in text


def _curve(z, b):
    return pd.DataFrame({"effect_pp": [0.0, 2.5, 5.0], "z_rate": [0.05] + z, "binomial_rate": [0.05] + b})


def test_power_direction_cases():
    assert power_direction(_curve([.2, .5], [.2, .5]))[0] == "identical"
    assert power_direction(_curve([.3, .6], [.2, .5]))[0] == "z"
    assert power_direction(_curve([.1, .4], [.2, .5]))[0] == "binomial"
    code, z_more, b_more = power_direction(_curve([.3, .4], [.2, .5]))
    assert (code, z_more, b_more) == ("mixed", [2.5], [5.0])
    assert "muda de lado" in power_sentence(_curve([.3, .4], [.2, .5]))


def test_conclusion_warns_until_group_fills_text(results_dir):
    at = run_app()
    warnings = " ".join(w.value for w in at.warning)
    assert "EXPECTATIVA_PREVIA" in warnings and "RECOMENDACAO" in warnings