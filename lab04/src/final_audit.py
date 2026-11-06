"""Auditoria reproduzível da base estatística do dashboard final (Issue #84).

Não substitui a inspeção dos gráficos G1–G4 e dos dados reais.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from pathlib import Path

REQUIRED_COLUMNS = (
    "n", "p0", "alpha", "seed", "p_true", "effect_pp", "repetitions",
    "z_rejections", "binomial_rejections", "z_rejection_rate",
    "binomial_rejection_rate", "z_monte_carlo_se", "binomial_monte_carlo_se",
)


def audit_s02_rows(rows: list[dict], *, min_effects: int = 5) -> list[str]:
    """Retorna uma lista de problemas de dados, sem assumir qual teste vence."""
    errors: list[str] = []
    if not rows:
        return ["Nenhum cenário de simulação encontrado"]
    if len(rows) < min_effects:
        errors.append(f"Esperados ao menos {min_effects} tamanhos de efeito")
    seen_effects: set[float] = set()
    reference: tuple[int, float, float, int, int] | None = None
    zero_effect_present = False
    for index, row in enumerate(rows, 1):
        prefix = f"Cenário {index}"
        missing = [name for name in REQUIRED_COLUMNS if name not in row]
        if missing:
            errors.append(f"{prefix}: colunas ausentes: {', '.join(missing)}")
            continue
        try:
            n, seed, repetitions = (int(row[k]) for k in ("n", "seed", "repetitions"))
            p0, alpha, p_true, effect = (float(row[k]) for k in ("p0", "alpha", "p_true", "effect_pp"))
            z_count, b_count = (int(row[k]) for k in ("z_rejections", "binomial_rejections"))
            z_rate, b_rate = (float(row[k]) for k in ("z_rejection_rate", "binomial_rejection_rate"))
            z_se, b_se = (float(row[k]) for k in ("z_monte_carlo_se", "binomial_monte_carlo_se"))
        except (ValueError, TypeError, OverflowError) as exc:
            errors.append(f"{prefix}: valores numéricos inválidos: {exc}")
            continue
        numbers = (p0, alpha, p_true, effect, z_rate, b_rate, z_se, b_se)
        if not all(math.isfinite(x) for x in numbers):
            errors.append(f"{prefix}: número não finito")
            continue
        if n < 1 or seed < 0 or repetitions != 10_000 or not 0 < p0 < 1 or not 0 < alpha < 1:
            errors.append(f"{prefix}: parâmetros inválidos ou != 10.000 repetições")
            continue
        metadata = (n, p0, alpha, seed, repetitions)
        if reference is None:
            reference = metadata
        elif reference != metadata:
            errors.append(f"{prefix}: metadados inconsistentes entre cenários")
        if not 0 <= p_true <= 1 or p_true < p0 - 1e-12:
            errors.append(f"{prefix}: hipótese alternativa fora do intervalo esperado")
        if not math.isclose(effect, 100 * (p_true - p0), abs_tol=1e-8):
            errors.append(f"{prefix}: efeito em pontos percentuais não corresponde a p_true - p0")
        if abs(effect) < 1e-8:
            zero_effect_present = True
        rounded_effect = round(effect, 8)
        if rounded_effect in seen_effects:
            errors.append(f"{prefix}: tamanho de efeito duplicado")
        seen_effects.add(rounded_effect)
        for label, count, rate, se in (("Z", z_count, z_rate, z_se), ("binomial", b_count, b_rate, b_se)):
            if not 0 <= count <= repetitions:
                errors.append(f"{prefix} {label}: contagem de rejeições inválida")
            elif not math.isclose(rate, count / repetitions, abs_tol=1e-12):
                errors.append(f"{prefix} {label}: taxa não confere com rejeições/repetições")
            if not 0 <= rate <= 1:
                errors.append(f"{prefix} {label}: taxa fora de [0,1]")
            elif not math.isclose(se, math.sqrt(rate * (1 - rate) / repetitions), abs_tol=1e-10):
                errors.append(f"{prefix} {label}: erro padrão de Monte Carlo incorreto")
    if not zero_effect_present:
        errors.append("Falta o cenário de efeito zero (H0 verdadeira / Q1)")
    return errors


def read_s02_csv(path: str | Path) -> list[dict]:
    with Path(path).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def audit_s02_csv(path: str | Path, *, replay: bool = False) -> dict:
    """Inspeciona o CSV e, opcionalmente, reexecuta as simulações pela seed."""
    file_path = Path(path)
    if not file_path.exists():
        return {"status": "pendente", "path": str(file_path), "problems": ["CSV não encontrado"]}
    rows = read_s02_csv(file_path)
    errors = audit_s02_rows(rows)
    if replay and not errors:
        from lab04.src.s02_experiments import run_experiments
        first = rows[0]
        generated = run_experiments(
            n=int(first["n"]),
            p_values=[float(row["p_true"]) for row in rows],
            repetitions=int(first["repetitions"]),
            seed=int(first["seed"]),
            p0=float(first["p0"]),
            alpha=float(first["alpha"]),
        )
        for i, (saved, current) in enumerate(zip(rows, generated), 1):
            for key in REQUIRED_COLUMNS:
                if not math.isclose(float(saved[key]), float(current[key]), rel_tol=1e-10, abs_tol=1e-10):
                    errors.append(f"Cenário {i}: {key} não se reproduz com a seed declarada")
    return {
        "status": "aprovado" if not errors else "falhou",
        "path": str(file_path),
        "scenarios": len(rows),
        "replayed": bool(replay and not errors),
        "problems": errors,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Lab04 auditoria estatística de Q1/Q2")
    parser.add_argument("--csv", default="lab04/results/s02_q1_q2.csv")
    parser.add_argument("--replay", action="store_true", help="Reproduz o CSV com a seed declarada")
    args = parser.parse_args()
    report = audit_s02_csv(args.csv, replay=args.replay)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["status"] != "aprovado":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
