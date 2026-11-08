"""Achados calculados das tabelas simuladas (G3/G4) para a seção 7 e para a legenda do G4.

Nada aqui declara vencedor: descreve o que foi observado em cada condição.
"""

from __future__ import annotations

import numpy as np

from lab04.src.formatting import num, pct, pp

TOL = 1e-12


def power_direction(g) -> tuple[str, list[float], list[float]]:
    """Compara as taxas de rejeição nos efeitos > 0 de UMA condição.

    Retorna (código, efeitos em que Z > binomial, efeitos em que binomial > Z) com código em
    "identical", "z", "binomial" ou "mixed" (a vantagem muda de lado).
    """
    pos = g[g["effect_pp"] > 1e-8]
    d = (pos["z_rate"] - pos["binomial_rate"]).to_numpy()
    eff = pos["effect_pp"].to_numpy()
    z_more = [float(e) for e, x in zip(eff, d) if x > TOL]
    b_more = [float(e) for e, x in zip(eff, d) if x < -TOL]
    if not z_more and not b_more:
        return "identical", z_more, b_more
    if not b_more:
        return "z", z_more, b_more
    if not z_more:
        return "binomial", z_more, b_more
    return "mixed", z_more, b_more


def power_sentence(g) -> str:
    """Frase curta sobre uma condição (sem o nome da condição)."""
    code, z_more, b_more = power_direction(g)
    pos = g[g["effect_pp"] > 1e-8]
    maxdiff = (pos["z_rate"] - pos["binomial_rate"]).abs()
    i = maxdiff.idxmax()
    at = f"{pp(100 * maxdiff[i])} no efeito de {num(pos.loc[i, 'effect_pp'], 1)} pp"
    if code == "identical":
        return "as taxas dos dois testes foram idênticas em todos os efeitos (as curvas se sobrepõem)"
    if code == "z":
        return f"o Z rejeitou mais que o binomial exato em todos os efeitos em que diferiram (até {at})"
    if code == "binomial":
        return f"o binomial exato rejeitou mais que o Z em todos os efeitos em que diferiram (até {at})"
    fmt = lambda xs: ", ".join(num(x, 1) for x in xs)  # noqa: E731
    return (f"a vantagem muda de lado: o Z rejeitou mais nos efeitos de {fmt(z_more)} pp "
            f"e o binomial exato nos de {fmt(b_more)} pp (diferença máxima {at})")


def type1_findings(t1) -> list[str]:
    return [
        f"{r.condition}: Z rejeitou {pct(r.z_rate)} sob H0 ({r.z_status}); "
        f"binomial exato {pct(r.binomial_rate)} ({r.binomial_status}); α = {pct(r.alpha, 0)}."
        for r in t1.itertuples()
    ]


def power_findings(pw) -> list[str]:
    return [f"{cond}: {power_sentence(g)}." for cond, g in pw.groupby("condition", sort=False)]


def limitations(real_df, real_n: int, sim_conditions: list[str]) -> list[str]:
    """Ressalvas verdadeiras por construção do estudo; números vêm dos dados."""
    first = real_df.iloc[0]
    return [
        f"Os dados reais vêm de um único repositório ({first['repository']}), uma única workflow "
        f"({first['workflow_name']}) e uma única branch ({first['branch']}), em "
        f"{real_df['created_at'].min()[:10]} a {real_df['created_at'].max()[:10]}; "
        f"não generalizam para outros projetos ou períodos.",
        "O modelo assume execuções independentes com probabilidade de falha constante; falhas de CI "
        "podem ser correlacionadas e variar no tempo.",
        "Os resultados de G3 e G4 são estimativas de Monte Carlo (erro-padrão de até cerca de 0,5 pp com "
        "10.000 repetições) e valem para as condições simuladas"
        + (": " + "; ".join(sim_conditions) if sim_conditions else "") + ".",
        f"Com n = {real_n} nos dados reais, um resultado não significativo não distingue ausência de efeito "
        "de amostra pequena demais para detectá-lo.",
    ]