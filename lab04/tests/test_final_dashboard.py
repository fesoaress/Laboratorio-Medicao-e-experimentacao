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


def conclusion_text(at):
    elements = list(at.main)
    start = next(i for i, element in enumerate(elements)
                 if element.type == "header" and element.value == "7. Conclusão")
    return "\n".join(element.value for element in elements[start:] if element.type == "markdown")


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


def test_conclusion_uses_versioned_results(monkeypatch):
    monkeypatch.delenv("LAB04_RESULTS_DIR", raising=False)
    at = run_app()
    assert not at.exception
    conclusion = conclusion_text(at)
    q1 = next(line for line in conclusion.splitlines() if "Q1 · Erro tipo I" in line)
    assert q1.count("4,48%") == 2 and "0,52 pp" in q1
    for expected in ("169 execuções", "7 falharam (4,14%)", "-0,86 p.p.", "rejeitar H₀",
                     "evidência", "não comprova", "n = 200, as curvas coincidiram",
                     "A 2,5 pp de efeito, o poder foi de 18,56% no Z e 7,10% no binomial exato",
                     "1,5 falhas", "6,05% para o Z (liberal)",
                     "1,69% para o binomial exato (conservador)"):
        assert expected in conclusion


def test_default_dashboard_has_explainable_thresholds_and_power_example(results_dir):
    at = run_app()
    assert not at.exception
    md = " ".join(m.value for m in at.markdown)
    assert "teste Z **K ≥ 4** · binomial exato **K ≥ 5**" in md
    assert "p verdadeiro = 10%" in md
    assert "Amostras menores" not in md
    assert "erro tipo i" in md.lower() and "erro tipo ii" in md.lower()


def test_g2_selects_the_three_existing_samples_and_preserves_official_data(results_dir):
    from lab04 import app

    ctx = app.build_context(n=30, true_p=0.10, seed=42, p0=0.05, alpha=0.05)
    assert app.g2_selected_results(ctx, "sim_small") is ctx["sim_results"]
    assert app.g2_selected_results(ctx, "sim_reference") is ctx["reference_results"]
    assert app.g2_selected_results(ctx, "real") is ctx["real_results"]["tests"]
    assert app.g2_selected_results(ctx, "sim_reference")["n"] == 200
    assert (app.g2_selected_results(ctx, "real")["n"],
            app.g2_selected_results(ctx, "real")["k"]) == (169, 7)
    with pytest.raises(ValueError, match="Amostra G2 desconhecida"):
        app.g2_selected_results(ctx, "desconhecida")

    at = run_app()
    assert not at.exception and len(at.radio) == 1
    assert at.radio[0].value == "sim_small"
    assert "K ≥ 4" in " ".join(m.value for m in at.markdown)
    original_tables = [table.value.copy() for table in at.dataframe]
    original_conclusion = conclusion_text(at)

    at.radio[0].set_value("sim_reference").run()
    assert not at.exception and not at.error
    selected_captions = " ".join(c.value for c in at.caption)
    assert "n = 200" in selected_captions
    assert "K = " in selected_captions
    assert "p₀ = 5% e α = 5%" in selected_captions
    assert "teste Z **K ≥ 16** · binomial exato **K ≥ 16**" in " ".join(
        m.value for m in at.markdown
    )

    at.radio[0].set_value("real").run()
    assert not at.exception and not at.error
    selected_captions = " ".join(c.value for c in at.caption)
    assert "GitHub Actions · dados observados, sem simulação" in selected_captions
    assert "n = 169, K = 7 falhas" in selected_captions
    assert at.metric[0].value == "0,6956"
    assert at.metric[1].value == "0,7452"
    assert "Parâmetros oficiais fixos" in selected_captions

    at.sidebar.slider[1].set_value(0.10)
    at.sidebar.select_slider[0].set_value(0.01)
    at.run()
    assert not at.exception and not at.error
    assert at.radio[0].value == "real"
    assert at.metric[0].value == "0,6956"
    assert at.metric[1].value == "0,7452"
    assert "p₀ = 5% e α = 5%" in " ".join(c.value for c in at.caption)
    for actual, expected in zip([table.value for table in at.dataframe], original_tables):
        pd.testing.assert_frame_equal(actual, expected)
    assert conclusion_text(at) == original_conclusion

    at.radio[0].set_value("sim_reference").run()
    assert not at.exception and not at.error
    assert "p₀ = 10% e α = 1%" in " ".join(c.value for c in at.caption)
    assert at.radio[0].value == "sim_reference"


def test_exploration_changes_g2_and_preserves_official_results(results_dir):
    at = run_app()
    official_tables = [table.value.copy() for table in at.dataframe]
    initial_conclusion = conclusion_text(at)
    for expected in ("Z 5,20% e binomial exato 3,80%",
                     "A 2,5 pp de efeito, o poder foi de 9,00% no Z e 12,00% no binomial exato",
                     "0,60% para o Z (conservador)", "2,50% para o binomial exato (conservador)"):
        assert expected in initial_conclusion
    initial_p = at.metric[0].value
    at.sidebar.number_input[0].set_value(40)
    at.sidebar.number_input[1].set_value(250)
    at.sidebar.slider[0].set_value(0.15)
    at.sidebar.number_input[2].set_value(21)
    at.sidebar.slider[1].set_value(0.10)
    at.sidebar.select_slider[0].set_value(0.01)
    at.run()
    assert not at.exception and not at.error and not at.warning
    assert at.metric[0].value != initial_p
    text = " ".join(m.value for m in at.markdown) + " ".join(c.value for c in at.caption)
    assert "n = 250" in text and "n = 40" in text
    assert "Por que comparar os tamanhos?" in text
    assert "Comparação direta dos limiares" in text
    assert "Amostras menores" not in text
    assert any("p₀ = 10% e α = 1%" in c.value for c in at.caption)
    assert any("Hipóteses e α do cenário oficial (p₀ = 0,05, α = 0,05)" in c.value for c in at.caption)
    assert len(at.dataframe) == len(official_tables) == 3
    for table, original in zip(at.dataframe, official_tables):
        pd.testing.assert_frame_equal(table.value, original)
    conclusion = conclusion_text(at)
    assert conclusion == initial_conclusion
    for expected in ("Expectativa inicial", "Q1 · Erro tipo I", "Q2 · Poder", "Q3 · Aproximação normal",
                     "prefira o binomial exato"):
        assert expected in conclusion
