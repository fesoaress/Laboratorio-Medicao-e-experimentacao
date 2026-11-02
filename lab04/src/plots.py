"""Gráficos G1 e G2 do dashboard Lab04 (P4: Z para proporção × binomial exato).

Convenções de cor (usadas em TODOS os gráficos, inclusive G3/G4 na S02):
  - teste Z para proporção ........ azul
  - teste binomial exato .......... laranja
  - dados reais ................... verde-azulado
  - dados simulados ............... roxo
Todas as funções devolvem um ``matplotlib.figure.Figure`` (sem usar pyplot global),
prontas para ``st.pyplot(fig)``.
"""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.patches import Patch
from matplotlib.lines import Line2D
from scipy.stats import binom, norm

COLOR_Z = "#1f77b4"
COLOR_BINOMIAL = "#d95f02"
COLOR_REAL = "#2a9d8f"
COLOR_SIM = "#7b5ea7"
COLOR_REF = "#444444"

OUTCOME_LABELS = ["0 = sucesso", "1 = falha"]


def critical_k(n: int, p0: float, alpha: float) -> int | None:
    """Menor k tal que P(K >= k | n, p0) < alpha (região de rejeição do binomial exato).

    Retorna None se nem k = n atinge p-valor < alpha.
    """
    for k in range(0, n + 1):
        if binom.sf(k - 1, n, p0) < alpha:
            return k
    return None


def _counts(outcomes) -> tuple[int, int, int]:
    arr = np.asarray(outcomes)
    n = int(arr.size)
    k = int(np.count_nonzero(arr))
    return n, n - k, k


def plot_g1(real, simulated, p0: float = 0.05, sim_label: str = "Simulados") -> Figure:
    """G1: histogramas de 0/1 dos dados reais e simulados, lado a lado.

    As observações são binárias, então o "histograma" é uma contagem das duas
    categorias (sucesso/falha). A linha tracejada marca a contagem esperada
    se a taxa de falha fosse exatamente p0 (fronteira de H0).
    """
    fig = Figure(figsize=(10, 4.2), constrained_layout=True)
    axes = fig.subplots(1, 2, sharey=False)
    groups = [
        (axes[0], real, COLOR_REAL, "Dados reais (CI)"),
        (axes[1], simulated, COLOR_SIM, sim_label),
    ]
    for ax, data, color, title in groups:
        n, ok, fail = _counts(data)
        bars = ax.bar([0, 1], [ok, fail], width=0.6, color=color, edgecolor="black", alpha=0.85)
        for x, v in zip([0, 1], [ok, fail]):
            ax.text(x, v, f"{v}\n({v / n:.1%})", ha="center", va="bottom", fontsize=10)
        for x, exp in zip([0, 1], [n * (1 - p0), n * p0]):
            ax.hlines(exp, x - 0.33, x + 0.33, colors=COLOR_REF, linestyles="--", linewidth=1.6)
        ax.set_xticks([0, 1], OUTCOME_LABELS)
        ax.set_ylim(0, max(ok, fail, 1) * 1.28)
        ax.set_xlabel("Resultado da execução de CI (variável binária)")
        ax.set_ylabel("Número de execuções (contagem)")
        ax.set_title(f"{title} — n = {n}")
        handles = [
            Patch(facecolor=color, edgecolor="black", alpha=0.85, label=title),
            Line2D([0], [0], color=COLOR_REF, linestyle="--", label=f"Esperado se p = {p0:.0%}"),
        ]
        ax.legend(handles=handles, loc="upper right" if fail < ok else "upper left", fontsize=8)
    fig.suptitle("G1 — Execuções de CI: dados reais × simulados (0 = sucesso, 1 = falha)", fontsize=12)
    return fig


def plot_g2(results: dict) -> Figure:
    """G2: distribuição sob H0 de cada teste (unilateral à direita).

    Esquerda: binomial discreta de K sob H0 (teste binomial exato).
    Direita: normal padrão de Z sob H0 (aproximação do teste Z).
    Hachura = região de rejeição; preenchimento sólido = área do p-valor do
    MESMO exemplo (P(estatística >= valor observado | H0)).
    """
    n, k, p0, alpha = results["n"], results["k"], results["p0"], results["alpha"]
    z_obs, z_crit = results["z_statistic"], results["z_critical"]
    p_z, p_b = results["z_p_value"], results["binomial_p_value"]
    k_crit = critical_k(n, p0, alpha)

    fig = Figure(figsize=(12, 4.6), constrained_layout=True)
    ax_b, ax_z = fig.subplots(1, 2)

    # ---- Binomial exato (discreto) ----
    sd = math.sqrt(n * p0 * (1 - p0))
    k_max = min(n, int(max(k, k_crit if k_crit is not None else 0, math.ceil(n * p0 + 5 * sd)) + 2))
    ks = np.arange(0, k_max + 1)
    pmf = binom.pmf(ks, n, p0)
    light = "#f2c9a8"
    ax_b.bar(ks, pmf, color=light, edgecolor="gray", width=0.85)
    if k_crit is not None:
        mask = ks >= k_crit
        ax_b.bar(ks[mask], pmf[mask], color=light, edgecolor=COLOR_BINOMIAL, hatch="///", width=0.85)
    mask_p = ks >= k
    ax_b.bar(ks[mask_p], pmf[mask_p], color=COLOR_BINOMIAL, edgecolor="black", alpha=0.85, width=0.85)
    ax_b.axvline(k, color="black", linewidth=1.6)
    size_b = binom.sf(k_crit - 1, n, p0) if k_crit is not None else 0.0
    rej_txt = (f"Região de rejeição: K ≥ {k_crit} (prob. sob H0 = {size_b:.3f})"
               if k_crit is not None else "Região de rejeição vazia (n pequeno demais)")
    ax_b.legend(handles=[
        Patch(facecolor=light, edgecolor="gray", label="P(K = k) sob H0"),
        Patch(facecolor=light, edgecolor=COLOR_BINOMIAL, hatch="///", label=rej_txt),
        Patch(facecolor=COLOR_BINOMIAL, edgecolor="black", alpha=0.85,
              label=f"Área do p-valor: P(K ≥ {k}) = {p_b:.4f}"),
        Line2D([0], [0], color="black", linewidth=1.6, label=f"Observado: k = {k} de n = {n}"),
    ], fontsize=8, loc="upper right")
    ax_b.set_xlabel("Número de falhas K na amostra (contagem)")
    ax_b.set_ylabel("Probabilidade sob H0 (p = p0)")
    ax_b.set_title(f"Binomial exato: K ~ Bin(n={n}, p0={p0:g}), cauda direita")

    # ---- Z (aproximação normal) ----
    lo, hi = -4.0, max(4.0, z_obs + 1, z_crit + 1)
    xs = np.linspace(lo, hi, 800)
    ys = norm.pdf(xs)
    ax_z.plot(xs, ys, color=COLOR_Z, linewidth=2)
    xr = xs[xs >= z_crit]
    ax_z.fill_between(xr, norm.pdf(xr), facecolor="none", edgecolor=COLOR_Z, hatch="///", linewidth=0)
    xp = xs[xs >= max(z_obs, lo)]
    ax_z.fill_between(xp, norm.pdf(xp), color=COLOR_Z, alpha=0.55)
    ax_z.axvline(z_obs, color="black", linewidth=1.6)
    ax_z.axvline(z_crit, color=COLOR_Z, linestyle=":", linewidth=1.6)
    ax_z.legend(handles=[
        Line2D([0], [0], color=COLOR_Z, linewidth=2, label="Z ~ N(0, 1) sob H0"),
        Patch(facecolor="none", edgecolor=COLOR_Z, hatch="///",
              label=f"Região de rejeição: Z > {z_crit:.3f} (α = {alpha:g})"),
        Patch(facecolor=COLOR_Z, alpha=0.55, label=f"Área do p-valor: P(Z ≥ {z_obs:.2f}) = {p_z:.4f}"),
        Line2D([0], [0], color="black", linewidth=1.6, label=f"Observado: z = {z_obs:.2f}"),
    ], fontsize=8, loc="upper left")
    ax_z.set_xlabel("Estatística Z (desvios-padrão sob H0)")
    ax_z.set_ylabel("Densidade sob H0")
    ax_z.set_title("Teste Z: Z ~ N(0, 1), cauda direita")

    fig.suptitle(f"G2 — Distribuição sob H0 (p ≤ {p0:g}), amostra de n = {n} execuções com {k} falhas", fontsize=12)
    return fig
