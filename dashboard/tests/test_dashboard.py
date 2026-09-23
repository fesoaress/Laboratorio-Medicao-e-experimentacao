from lab02.dashboard.build_dashboard import final_rq3_summary, load_tables


def test_dashboard_uses_final_rq3_sample():
    tables = load_tables()
    summary = final_rq3_summary(tables["rq3_summary"], tables["rq3_detail"])

    assert len(tables["rq3_detail"]) == 12
    assert not tables["rq3_detail"].trial_id.str.startswith("SIM-").any()
    assert summary.groupby("tratamento").n.first().to_dict() == {
        "IA": 6,
        "Manual": 6,
    }
