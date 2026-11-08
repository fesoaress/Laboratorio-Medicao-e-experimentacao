"""Tamanho do efeito nos dados reais (h de Cohen e IC exato); a tabela e a decisão ficam em real_results."""

from __future__ import annotations

import math

from scipy.stats import binomtest

from lab04.src.formatting import num, pct


def cohens_h(p1: float, p2: float) -> float:
    """h de Cohen para duas proporções: 2·asin(√p1) − 2·asin(√p2)."""
    return 2 * math.asin(math.sqrt(p1)) - 2 * math.asin(math.sqrt(p2))


def h_magnitude(h: float) -> str:
    a = abs(h)
    return "desprezível" if a < 0.2 else "pequeno" if a < 0.5 else "médio" if a < 0.8 else "grande"


def effect_summary(k: int, n: int, p0: float) -> dict:
    """Efeito observado: p̂ − p0 (pp), h de Cohen e IC exato de 95% para p (Clopper-Pearson)."""
    p_hat = k / n
    ci = binomtest(k, n, p0).proportion_ci(confidence_level=0.95, method="exact")
    h = cohens_h(p_hat, p0)
    return {"p_hat": p_hat, "diff_pp": 100 * (p_hat - p0), "h": h, "h_label": h_magnitude(h),
            "ci_low": float(ci.low), "ci_high": float(ci.high)}


def effect_text(eff: dict) -> str:
    """Complemento do texto de ``real_results.interpret_real_results`` com o tamanho do efeito."""
    return (f"Tamanho do efeito: h de Cohen = {num(eff['h'])} ({eff['h_label']}); o intervalo exato de 95% "
            f"para a taxa real vai de {pct(eff['ci_low'])} a {pct(eff['ci_high'])}.")