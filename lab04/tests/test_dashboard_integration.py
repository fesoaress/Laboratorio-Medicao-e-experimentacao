"""Testes da camada de dados para a integração do dashboard (#84)."""

import csv
import math

from lab04.src.final_audit import REQUIRED_COLUMNS, audit_s02_csv, audit_s02_rows


def valid_rows():
    values = [0.05, 0.075, 0.10, 0.125, 0.15, 0.20]
    counts = [448, 4395, 8599, 9832, 9990, 10000]
    rows = []
    for p, k in zip(values, counts):
        rate = k / 10_000
        rows.append({
            "n": 200, "p0": 0.05, "alpha": 0.05, "seed": 42,
            "p_true": p, "effect_pp": 100 * (p - 0.05),
            "repetitions": 10_000, "z_rejections": k,
            "binomial_rejections": k,
            "z_rejection_rate": rate, "binomial_rejection_rate": rate,
            "z_monte_carlo_se": math.sqrt(rate * (1 - rate) / 10_000),
            "binomial_monte_carlo_se": math.sqrt(rate * (1 - rate) / 10_000),
        })
    return rows


def test_valid_s02_scenarios():
    assert audit_s02_rows(valid_rows()) == []


def test_missing_zero_effect_is_caught():
    rows = valid_rows()[1:]
    assert any("efeito zero" in item for item in audit_s02_rows(rows))


def test_rate_inconsistent_with_rejection_count_is_caught():
    rows = valid_rows()
    rows[2]["binomial_rejection_rate"] += 0.01
    assert any("taxa não confere" in item for item in audit_s02_rows(rows))


def test_wrong_effect_is_caught():
    rows = valid_rows()
    rows[3]["effect_pp"] = 900
    assert any("efeito em pontos percentuais" in item for item in audit_s02_rows(rows))


def test_wrong_monte_carlo_se_is_caught():
    rows = valid_rows()
    rows[1]["z_monte_carlo_se"] = 0
    assert any("erro padrão" in item for item in audit_s02_rows(rows))


def test_non_10000_repetitions_is_caught():
    rows = valid_rows()
    rows[0]["repetitions"] = 100
    assert any("10.000 repetições" in item for item in audit_s02_rows(rows))


def test_inconsistent_parameters_are_caught():
    rows = valid_rows()
    rows[2]["alpha"] = 0.01
    assert any("metadados inconsistentes" in item for item in audit_s02_rows(rows))


def test_missing_column_is_caught():
    rows = valid_rows()
    del rows[2]["p_true"]
    assert any("colunas ausentes" in item for item in audit_s02_rows(rows))


def test_nonfinite_value_is_caught():
    rows = valid_rows()
    rows[1]["z_rejection_rate"] = float("nan")
    assert any("não finito" in item for item in audit_s02_rows(rows))


def test_duplicate_effect_is_caught():
    rows = valid_rows()
    rows[1]["p_true"] = rows[0]["p_true"]
    rows[1]["effect_pp"] = rows[0]["effect_pp"]
    assert any("duplicado" in item for item in audit_s02_rows(rows))


def test_audit_can_read_csv(tmp_path):
    path = tmp_path / "samples.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=REQUIRED_COLUMNS)
        writer.writeheader()
        writer.writerows(valid_rows())
    report = audit_s02_csv(path)
    assert report["status"] == "aprovado"
    assert report["scenarios"] == 6


def test_unavailable_csv_is_pending(tmp_path):
    report = audit_s02_csv(tmp_path / "missing.csv")
    assert report["status"] == "pendente"
