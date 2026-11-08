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
from matplotlib.ticker import PercentFormatter
from scipy.stats import binom, norm

from lab04.src.formatting import p_value

COLOR_Z = "#1f77b4"
COLOR_BINOMIAL = "#d95f02"
COLOR_REAL = "#2a9d8f"
COLOR_SIM = "#7b5ea7"
COLOR_REF = "#444444"

OUTCOME_LABELS = ["0 = sucesso", "1 = falha"]


def _pt(text: str) -> str:
    """Vírgula decimal nos textos dos gráficos (rótulos, legendas, títulos)."""
    return text.replace(".", ",")


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
    fig = Figure(figsize=(8, 3.6), constrained_layout=True)
    axes = fig.subplots(1, 2, sharey=False)
    groups = [
        (axes[0], real, COLOR_REAL, "Dados reais (CI)"),
        (axes[1], simulated, COLOR_SIM, sim_label),
    ]
    for ax, data, color, title in groups:
        n, ok, fail = _counts(data)
        ax.bar([0, 1], [ok, fail], width=0.6, color=color, edgecolor="black", alpha=0.85)
        expected = [n * (1 - p0), n * p0]
        top = max(ok, fail, *expected, 1)
        for x, v, exp in zip([0, 1], [ok, fail], expected):
            ax.text(x, max(v, exp) + top * 0.02, _pt(f"{v}\n({v / n:.1%})"), ha="center", va="bottom", fontsize=10)
        for x, exp in zip([0, 1], expected):
            ax.hlines(exp, x - 0.33, x + 0.33, colors=COLOR_REF, linestyles="--", linewidth=1.6)
        ax.set_xticks([0, 1], OUTCOME_LABELS)
        ax.set_ylim(0, top * 1.35)
        ax.set_ylabel("Execuções")
        ax.set_title(f"{title} — n = {n}")
        handles = [
            Patch(facecolor=color, edgecolor="black", alpha=0.85, label=title),
            Line2D([0], [0], color=COLOR_REF, linestyle="--", label=f"Esperado se p = {p0:.0%}"),
        ]
        ax.legend(handles=handles, loc="upper right" if fail < ok else "upper left", fontsize=8)
    fig.suptitle("G1 — Resultados reais e simulados de CI", fontsize=14)
    return fig


def plot_g2(results: dict) -> Figure:
    """G2: distribuição sob H0 de cada teste (unilateral à direita).

    Painéis: binomial discreta de K e normal padrão de Z sob H0.
    Hachura = região de rejeição; preenchimento sólido = área do p-valor do
    MESMO exemplo (P(estatística >= valor observado | H0)).
    """
    n, k, p0, alpha = results["n"], results["k"], results["p0"], results["alpha"]
    z_obs, z_crit = results["z_statistic"], results["z_critical"]
    p_z, p_b = results["z_p_value"], results["binomial_p_value"]
    k_crit = critical_k(n, p0, alpha)

    fig = Figure(figsize=(7, 6.4), constrained_layout=True)
    ax_b, ax_z = fig.subplots(2, 1)

    # ---- Binomial exato (discreto) ----
    sd = math.sqrt(n * p0 * (1 - p0))
    k_max = min(n, int(max(k, k_crit if k_crit is not None else 0, math.ceil(n * p0 + 5 * sd)) + 2))
    ks = np.arange(0, k_max + 1)
    pmf = binom.pmf(ks, n, p0)
    light = "#f2c9a8"
    ax_b.bar(ks, pmf, color=light, edgecolor="gray", width=0.85)
    mask_p = ks >= k
    ax_b.bar(ks[mask_p], pmf[mask_p], color=COLOR_BINOMIAL, edgecolor="black", alpha=0.85, width=0.85)
    if k_crit is not None:
        mask = ks >= k_crit
        ax_b.bar(ks[mask], pmf[mask], facecolor="none", edgecolor="#733500", hatch="///", width=0.85)
    ax_b.axvline(k, color="black", linewidth=1.6)
    size_b = binom.sf(k_crit - 1, n, p0) if k_crit is not None else 0.0
    rej_txt = (_pt(f"Região de rejeição: K ≥ {k_crit} (prob. sob H0 = {size_b:.3f})")
               if k_crit is not None else "Região de rejeição vazia (n pequeno demais)")
    ax_b.legend(handles=[
        Patch(facecolor=light, edgecolor="gray", label="P(K = k) sob H0"),
        Patch(facecolor="none", edgecolor="#733500", hatch="///", label=rej_txt),
        Patch(facecolor=COLOR_BINOMIAL, edgecolor="black", alpha=0.85,
              label=f"Cauda P(K ≥ {k}) · p-valor {p_value(p_b)}"),
        Line2D([0], [0], color="black", linewidth=1.6, label=f"Observado: k = {k} de n = {n}"),
    ], fontsize=8, loc="upper right")
    ax_b.set_ylim(0, ax_b.get_ylim()[1] * 1.3)
    ax_b.set_xlabel("Número de falhas K na amostra (contagem)")
    ax_b.set_ylabel("Probabilidade sob H0 (p = p0)")
    ax_b.set_title(_pt(f"Binomial exato: K ~ Bin(n={n}, p0={p0:g}), cauda direita"))

    # ---- Z (aproximação normal) ----
    lo, hi = min(-4.0, z_obs - 0.5), max(4.0, z_obs + 1, z_crit + 1)
    xs = np.unique(np.r_[np.linspace(lo, hi, 800), z_obs, z_crit])
    ys = norm.pdf(xs)
    ax_z.plot(xs, ys, color=COLOR_Z, linewidth=2)
    xr = xs[xs >= z_crit]
    xp = xs[xs >= z_obs]
    ax_z.fill_between(xp, norm.pdf(xp), color=COLOR_Z, alpha=0.55)
    ax_z.fill_between(xr, norm.pdf(xr), facecolor="none", edgecolor=COLOR_Z, hatch="///", linewidth=0)
    ax_z.axvline(z_obs, color="black", linewidth=1.6)
    ax_z.axvline(z_crit, color=COLOR_Z, linestyle=":", linewidth=1.6)
    ax_z.legend(handles=[
        Line2D([0], [0], color=COLOR_Z, linewidth=2, label="Z ~ N(0, 1) sob H0"),
        Patch(facecolor="none", edgecolor=COLOR_Z, hatch="///",
              label=_pt(f"Região de rejeição: Z > {z_crit:.3f} (α = {alpha:g})")),
        Patch(facecolor=COLOR_Z, alpha=0.55, label=f"Cauda à direita de z · p-valor {p_value(p_z)}"),
        Line2D([0], [0], color="black", linewidth=1.6, label=_pt(f"Observado: z = {z_obs:.2f}")),
    ], fontsize=8, loc="upper left")
    ax_z.set_ylim(0, 0.62)
    ax_z.set_xlabel("Estatística Z (desvios-padrão sob H0)")
    ax_z.set_ylabel("Densidade sob H0")
    ax_z.set_title("Teste Z: Z ~ N(0, 1), cauda direita")

    fig.suptitle(_pt(f"G2 — Distribuições na fronteira p = {p0:g} de H₀"), fontsize=14)
    return fig


# ----------------------------------------------------------------------------- S02 (G3 e G4)
STATUS_SHORT = {"liberal": "liberal", "conservador": "conservador", "compatível com α": "≈ α"}
CONDITION_STYLES = [("-", "o"), ("--", "s"), (":", "^"), ("-.", "D")]


def plot_g3(t1) -> Figure:
    """G3: erro tipo I de Z e binomial exato em cada condição simulada.

    ``t1`` é a saída de ``s02_results.type1_table``. As barras mostram a proporção de
    rejeições sob H0; as barras de erro são ±1,96 erro-padrão de Monte Carlo; a linha
    horizontal marca α. O rótulo (liberal / conservador / ≈ α) vem da própria tabela.
    """
    conditions = list(t1["condition"])
    alpha = float(t1["alpha"].iloc[0])
    fig = Figure(figsize=(max(7, 2.5 * len(conditions) + 2), 4.2), constrained_layout=True)
    ax = fig.subplots()
    width = 0.36
    xs = np.arange(len(conditions))
    top = alpha
    for offset, key, color, name in ((-width / 2, "z", COLOR_Z, "Z para proporção"),
                                     (width / 2, "binomial", COLOR_BINOMIAL, "Binomial exato")):
        rates = t1[f"{key}_rate"].to_numpy()
        ses = t1[f"{key}_se"].to_numpy()
        ax.bar(xs + offset, rates, width, color=color, edgecolor="black", alpha=0.9, label=name)
        ax.errorbar(xs + offset, rates, yerr=1.96 * ses, fmt="none", ecolor="black", capsize=4, linewidth=1.2)
        for x, r, se, status in zip(xs + offset, rates, ses, t1[f"{key}_status"]):
            ax.text(x, r + 1.96 * se + alpha * 0.04,
                    f"{100 * r:.2f}%".replace(".", ",") + f"\n{STATUS_SHORT[status]}",
                    ha="center", va="bottom", fontsize=8)
            top = max(top, r + 1.96 * se)
    ax.axhline(alpha, color="black", linestyle="--", linewidth=1.4, label=f"α = {alpha:.0%}")
    ax.set_ylim(0, top * 1.35)
    ax.set_xticks(xs, [c.replace(" (", "\n(") for c in conditions])
    ax.set_xlabel("Condição simulada")
    ax.set_ylabel("Rejeições sob H₀")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_title("G3 — Erro tipo I por condição", fontsize=14)
    ax.legend(loc="upper left", fontsize=9)
    return fig


def plot_g4(pw) -> Figure:
    """G4: curvas de poder de Z e binomial exato no mesmo gráfico.

    ``pw`` é a saída de ``s02_results.power_table``. Cor = teste (igual ao G3);
    estilo da linha/marcador = condição simulada. O efeito 0 é o erro tipo I.
    """
    alpha = float(pw["alpha"].iloc[0])
    fig = Figure(figsize=(7.5, 4.5), constrained_layout=True)
    ax = fig.subplots()
    ax.axhline(alpha, color="gray", linestyle=":", linewidth=1.2, label=f"α = {alpha:.0%}")
    for i, (cond, g) in enumerate(pw.groupby("condition", sort=False)):
        ls, mk = CONDITION_STYLES[i % len(CONDITION_STYLES)]
        g = g.sort_values("effect_pp")
        # Z mais grosso e translúcido, binomial fino por cima: se as curvas coincidirem,
        # as duas continuam visíveis (uma não esconde a outra).
        ax.plot(g["effect_pp"], g["z_rate"], color=COLOR_Z, linestyle=ls, marker=mk, linewidth=5,
                markersize=11, alpha=0.6, label=f"Z — {cond}", zorder=2)
        ax.plot(g["effect_pp"], g["binomial_rate"], color=COLOR_BINOMIAL, linestyle=ls, marker=mk,
                linewidth=1.8, markersize=5, label=f"Binomial exato — {cond}", zorder=3)
    ax.set_xlim(left=0)
    ax.set_ylim(-0.02, 1.02)
    ax.set_xlabel("Tamanho do efeito (p real − p0, em pontos percentuais)")
    ax.set_ylabel("Rejeições")
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
    ax.set_title("G4 — Poder por tamanho de efeito", fontsize=14)
    ax.legend(loc="lower right", fontsize=8)
    return fig
