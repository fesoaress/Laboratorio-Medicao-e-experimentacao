"""Comparações de poder e limitações do Lab04."""

from __future__ import annotations

from lab04.src.formatting import num, pp

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
    if pos.empty:
        return "a tabela contém apenas o efeito zero, que estima o erro tipo I"
    if code == "identical":
        return "as taxas dos dois testes foram idênticas em todos os efeitos positivos"
    maxdiff = (pos["z_rate"] - pos["binomial_rate"]).abs()
    i = maxdiff.idxmax()
    at = f"{pp(100 * maxdiff[i])} no efeito de {num(pos.loc[i, 'effect_pp'], 1)} pp"
    if code == "z":
        return f"o Z rejeitou mais que o binomial exato em todos os efeitos em que diferiram (até {at})"
    if code == "binomial":
        return f"o binomial exato rejeitou mais que o Z em todos os efeitos em que diferiram (até {at})"
    fmt = lambda xs: ", ".join(num(x, 1) for x in xs)  # noqa: E731
    return (f"a vantagem muda de lado: o Z rejeitou mais nos efeitos de {fmt(z_more)} pp "
            f"e o binomial exato nos de {fmt(b_more)} pp (diferença máxima {at})")


def limitations(real_n: int) -> list[str]:
    """Limites da inferência observacional e das estimativas de Monte Carlo."""
    return [
        "A coleta abrange um workflow, uma branch e um período. Execuções próximas podem compartilhar "
        "causas de falha, enquanto o modelo supõe independência e probabilidade constante.",
        "As taxas de G3 e G4 são estimativas de Monte Carlo para as condições simuladas.",
        f"Com n = {real_n}, diferenças pequenas em relação à meta podem passar despercebidas.",
    ]
