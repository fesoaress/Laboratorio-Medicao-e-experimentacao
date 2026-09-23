from lab02.analysis.analyze_rq1_rq2 import analyze, load_and_audit
from lab02.analysis.analyze_rq3 import load_detail


def test_final_rq1_rq2_sample_has_three_complete_participants():
    audit, trials, cycles = load_and_audit()

    assert len(trials) == 12
    assert set(trials.participante) == {"Fernanda", "Islayder", "Vinicius"}
    assert not trials.trial_id.str.startswith("SIM-").any()
    for _, group in trials.groupby("participante"):
        assert len(group) == 4
        assert group.kata.nunique() == 4
        assert group.tratamento.value_counts().to_dict() == {"IA": 2, "Manual": 2}

    tables = analyze(audit, trials, cycles)
    rq1 = tables["rq1_resumo"].set_index("tratamento")
    assert rq1.loc["IA", "n_trials"] == 6
    assert rq1.loc["Manual", "n_trials"] == 6
    assert tables["rq1_wilcoxon"].iloc[0].n_pares == 3


def test_final_rq3_has_no_simulated_or_incomplete_metrics():
    detail = load_detail(require_fernanda=True)

    assert len(detail) == 12
    assert not detail.trial_id.str.startswith("SIM-").any()
    assert detail.metricas_completas.all()
    assert detail.analysis_error.eq("").all()
