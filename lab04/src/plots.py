"""Figuras G1–G4 do Lab04, com azul para Z e laranja para o binomial exato."""

from __future__ import annotations

import math

import numpy as np
from matplotlib.figure import Figure
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator, PercentFormatter, StrMethodFormatter
from scipy.stats import binom, norm

from lab04.src.formatting import num, pct, p_value

COLOR_Z = "#1f77b4"
COLOR_BINOMIAL = "#d95f02"
COLOR_REAL = "#176c65"
COLOR_SIM = "#6b4e90"
COLOR_OBS = "#162432"
COLOR_CRIT = "#586673"
COLOR_GRID = "#dee5eb"

OUTCOME_LABELS = ["0 = sucesso", "1 = falha"]


def _figure(title: str, height: float, width: float = 5.8) -> Figure:
    fig = Figure(figsize=(width, height), layout="constrained", facecolor="#ffffff")
    fig.suptitle(title, fontsize=15, fontweight="bold", color=COLOR_OBS)
    return fig


def _style(ax) -> None:
    ax.spines[["top", "right"]].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(COLOR_CRIT)
    ax.tick_params(labelsize=10, colors=COLOR_OBS)
    ax.set_axisbelow(True)
    ax.grid(axis="y", color=COLOR_GRID)


def critical_k(n: int, p0: float, alpha: float) -> int | None:
    """Menor k tal que P(K >= k | n, p0) < alpha, ou None."""
    for k in range(n + 1):
        if binom.sf(k - 1, n, p0) < alpha:
            return k
    return None


def critical_k_z(n: int, p0: float, alpha: float) -> int | None:
    """Menor k com p-valor unilateral do Z estritamente inferior a alpha."""
    stderr = math.sqrt(p0 * (1 - p0) / n)
    for k in range(n + 1):
        z = (k / n - p0) / stderr
        if norm.sf(z) < alpha:
            return k
    return None


def plot_g1(real, simulated, reference, p0: float = 0.05,
            sim_label: str = "Simulação ajustável") -> Figure:
    """G1: dados reais e duas amostras simuladas, em escalas percentuais iguais.

    As duas amostras de G1 são exemplos ilustrativos; G3/G4 usam as tabelas
    oficiais de 10.000 repetições por cenário.
    """
    # Painéis empilhados preservam a leitura também em telas estreitas.
    fig = _figure("G1 · Resultados de CI", 6.6)
    axes = fig.subplots(3, 1, sharey=True)
    expected = [1 - p0, p0]
    groups = (
        (real, COLOR_REAL, "Dados reais"),
        (simulated, COLOR_SIM, sim_label),
        (reference, COLOR_SIM, "Simulação de referência"),
    )
    for ax, (outcomes, color, label) in zip(axes, groups):
        n = len(outcomes)
        failures = int(np.count_nonzero(outcomes))
        counts = np.array([n - failures, failures])
        rates = counts / n
        _style(ax)
        ax.bar([0, 1], rates, width=0.60, color=color)
        for x, (count, rate, target) in enumerate(zip(counts, rates, expected)):
            ax.hlines(target, x - 0.36, x + 0.36, colors=COLOR_OBS,
                      linestyles="--", linewidth=1.4)
            inside = rate > 0.68
            # Em barras altas, alinhar o rótulo pelo topo evita que a
            # linha de referência (95%/5%) atravesse o texto.
            y = rate - 0.07 if inside else rate + 0.04
            if not inside and abs(y - target) < 0.09:
                y = target + 0.04 if target < 0.9 else y - 0.09
            ax.text(x, y, f"{pct(rate)}\n{count}/{n}", ha="center",
                    va="top" if inside else "bottom",
                    color="white" if inside else COLOR_OBS, fontsize=11,
                    fontweight="bold")
        ax.set_xticks([0, 1], OUTCOME_LABELS)
        ax.set_xlim(-0.55, 1.55)
        ax.set_ylim(0, 1)
        ax.set_yticks([0, 0.25, 0.50, 0.75, 1])
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_ylabel("Frequência (%)", fontsize=10)
        ax.set_title(f"{label} · n = {n}", loc="left", fontsize=12, color=COLOR_OBS)
    fig.legend(handles=[Line2D([], [], color=COLOR_OBS, linestyle="--",
                               label=f"Esperado com taxa de falha de {pct(p0, 0)}")],
               loc="outside lower center", frameon=False, fontsize=10)
    return fig


def _observed_line(ax, observed: float, low: float, high: float) -> None:
    if low <= observed <= high:
        ax.axvline(observed, color=COLOR_OBS, linewidth=2.3, zorder=4)
    else:
        right = observed > high
        ax.text(0.98 if right else 0.02, 0.94, "Observado →" if right else "← Observado",
                transform=ax.transAxes, ha="right" if right else "left", va="top",
                color=COLOR_OBS, fontsize=11)


def plot_g2(results: dict) -> Figure:
    """G2: cauda observada sombreada e região de rejeição hachurada, sob H₀."""
    n, k, p0, alpha = results["n"], results["k"], results["p0"], results["alpha"]
    z_obs, z_crit = results["z_statistic"], results["z_critical"]
    k_crit = critical_k(n, p0, alpha)
    fig = _figure("G2 · Distribuições sob H₀", 6.6)
    ax_b, ax_z = fig.subplots(2, 1)
    for ax in (ax_b, ax_z):
        _style(ax)

    # Mantenha a massa visível quando uma amostra exploratória cai longe da fronteira.
    mean = n * p0
    sd = math.sqrt(n * p0 * (1 - p0))
    k_min = max(0, math.floor(mean - 5 * sd))
    k_max = min(n, max(math.ceil(mean + 5 * sd), (k_crit or 0) + 1))
    ks = np.arange(k_min, k_max + 1)
    pmf = binom.pmf(ks, n, p0)
    ax_b.bar(ks, pmf, color="#f6d9c5", edgecolor=COLOR_BINOMIAL, width=0.82, linewidth=0.6)
    tail = ks >= k
    ax_b.bar(ks[tail], pmf[tail], color=COLOR_BINOMIAL, width=0.82)
    if k_crit is not None:
        rejection = ks >= k_crit
        ax_b.bar(ks[rejection], pmf[rejection], facecolor="none",
                 edgecolor=COLOR_OBS, hatch="///", width=0.82)
        ax_b.axvline(k_crit, color=COLOR_CRIT, linestyle="--", linewidth=1.6, zorder=5)
    _observed_line(ax_b, k, k_min, k_max)
    ax_b.set_xlim(k_min - 0.6, k_max + 0.6)
    ax_b.set_ylim(0, max(pmf) * 1.36)
    # Probabilidade de cada contagem: rótulos de massa relevante, calculados
    # diretamente da PMF. Em explorações com muitas barras, espaçar os rótulos.
    label_indices = np.flatnonzero(pmf >= 0.0005)
    if len(label_indices) > 18:
        label_indices = label_indices[np.unique(
            np.linspace(0, len(label_indices) - 1, 18, dtype=int)
        )]
    for idx in label_indices:
        ax_b.annotate(
            pct(float(pmf[idx]), 2), (int(ks[idx]), float(pmf[idx])),
            xytext=(0, 4), textcoords="offset points", ha="center", va="bottom",
            fontsize=8, color=COLOR_OBS,
            bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.88, "pad": 0.1},
        )
    b_side = k > k_max
    ax_b.text(
        0.02 if b_side else 0.98, 0.98,
        f"Observado: K = {k}\\n"
        f"Crítico: {f'K ≥ {k_crit}' if k_crit is not None else 'sem rejeição'}\\n"
        f"p-valor = {p_value(results['binomial_p_value'])}",
        transform=ax_b.transAxes, ha="left" if b_side else "right", va="top",
        fontsize=9, fontweight="medium", color=COLOR_OBS,
        bbox={"facecolor": "white", "edgecolor": COLOR_BINOMIAL,
              "alpha": 0.96, "boxstyle": "round,pad=0.4"},
        zorder=7,
    )
    ax_b.xaxis.set_major_locator(MaxNLocator(nbins=7, integer=True))
    ax_b.yaxis.set_major_formatter(PercentFormatter(1, decimals=1))
    ax_b.set(xlabel="K · número de falhas", ylabel="Probabilidade (%)")
    ax_b.set_title(f"Binomial exato · K ∼ Bin({n}, {num(p0)})", loc="left", fontsize=12)

    lo, hi = -4.0, 4.0
    xs = np.unique(np.r_[np.linspace(lo, hi, 600), np.clip(z_obs, lo, hi), z_crit])
    ax_z.plot(xs, norm.pdf(xs), color=COLOR_Z, linewidth=2.0)
    tail_x = xs[xs >= z_obs]
    rejection_x = xs[xs >= z_crit]
    z_tail_alpha = 0.46
    ax_z.fill_between(tail_x, norm.pdf(tail_x), color=COLOR_Z, alpha=z_tail_alpha)
    ax_z.fill_between(rejection_x, norm.pdf(rejection_x), facecolor="none",
                      edgecolor=COLOR_OBS, hatch="///", linewidth=0)
    _observed_line(ax_z, z_obs, lo, hi)
    ax_z.axvline(z_crit, color=COLOR_CRIT, linestyle="--", linewidth=1.6, zorder=5)
    ax_z.set(xlim=(lo, hi), ylim=(0, 0.48), xlabel="Z · desvios-padrão sob H₀", ylabel="Densidade")
    ax_z.yaxis.set_major_formatter(StrMethodFormatter("{x:.1f}"))
    ax_z.set_title("Teste Z · aproximação normal N(0, 1)", loc="left", fontsize=12)
    z_side = z_obs > hi
    ax_z.text(
        0.02 if z_side else 0.98, 0.98,
        f"Observado: Z = {num(z_obs, 3)}\\n"
        f"Crítico: Z = {num(z_crit, 3)}\\n"
        f"p-valor = {p_value(results['z_p_value'])}",
        transform=ax_z.transAxes, ha="left" if z_side else "right", va="top",
        fontsize=9, fontweight="medium", color=COLOR_OBS,
        bbox={"facecolor": "white", "edgecolor": COLOR_Z,
              "alpha": 0.96, "boxstyle": "round,pad=0.4"},
        zorder=7,
    )

    fig.legend(handles=[
        Patch(facecolor=COLOR_BINOMIAL, label="Cauda do p-valor · binomial"),
        Patch(facecolor=COLOR_Z, alpha=z_tail_alpha, label="Cauda do p-valor · Z"),
        Patch(facecolor="white", edgecolor=COLOR_OBS, hatch="///", label="Região de rejeição"),
        Line2D([], [], color=COLOR_OBS, linewidth=2.3, label="Valor observado"),
        Line2D([], [], color=COLOR_CRIT, linestyle="--", label="Limiar crítico"),
    ], loc="outside lower center", ncols=2, frameon=False, fontsize=11)
    return fig


def plot_g3(t1) -> Figure:
    """G3: taxas de erro tipo I, com barras de Monte Carlo de ±1,96 EP."""
    alpha = float(t1["alpha"].iloc[0])
    fig = _figure("G3 · Erro tipo I por condição", 4.1, max(5.8, len(t1) * 2.1))
    ax = fig.subplots()
    _style(ax)
    width = 0.36
    xs = np.arange(len(t1))
    top = alpha
    for offset, key, color, name in ((-0.20, "z", COLOR_Z, "Teste Z"),
                                     (0.20, "binomial", COLOR_BINOMIAL, "Binomial exato")):
        rates = t1[f"{key}_rate"].to_numpy()
        errors = 1.96 * t1[f"{key}_se"].to_numpy()
        ax.bar(xs + offset, rates, width, color=color, label=name)
        ax.errorbar(xs + offset, rates, yerr=errors, fmt="none", ecolor=COLOR_OBS,
                    capsize=4, linewidth=1.2, zorder=3)
        for x, rate, error in zip(xs + offset, rates, errors):
            ax.annotate(pct(rate), (x, rate + error), xytext=(0, 4), textcoords="offset points",
                        ha="center", va="bottom", fontsize=11, color=COLOR_OBS)
        top = max(top, max(rates + errors))
    ax.axhline(alpha, color=COLOR_OBS, linestyle="--", linewidth=1.5, label=f"α = {pct(alpha, 0)}")
    ax.set_ylim(0, top * 1.21)
    ax.set_xticks(xs, [c.replace(" (", "\n(") for c in t1["condition"]])
    ax.set(xlabel="Condição simulada", ylabel="Taxa de erro tipo I (%)")
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=None))
    fig.legend(loc="outside lower center", ncols=3, frameon=False, fontsize=10)
    return fig


def plot_g4(pw) -> Figure:
    """G4: uma figura com um painel por condição, em escalas compartilhadas."""
    groups = list(pw.sort_values(["n", "effect_pp"]).groupby("condition", sort=False))
    fig = _figure("G4 · Poder por tamanho de efeito", 2.95 * len(groups) + 0.7)
    axes = fig.subplots(len(groups), 1, sharex=True, sharey=True, squeeze=False).ravel()
    effects = sorted(pw["effect_pp"].unique())
    for ax, (condition, group) in zip(axes, groups):
        _style(ax)
        ax.plot(group["effect_pp"], group["z_rate"], color=COLOR_Z, marker="o",
                markersize=7, linewidth=3, clip_on=False, label="Teste Z")
        ax.plot(group["effect_pp"], group["binomial_rate"], color=COLOR_BINOMIAL,
                linestyle="--", marker="D", markersize=4, linewidth=1.6,
                clip_on=False, label="Binomial exato")
        ax.set_title(condition, loc="left", fontsize=12)
        all_same = np.allclose(group["z_rate"], group["binomial_rate"],
                              atol=1e-12, rtol=0)
        if all_same:
            ax.text(0.98, 0.08, "Curvas coincidentes (Z = exato)",
                    ha="right", va="bottom", transform=ax.transAxes,
                    fontsize=10, color=COLOR_OBS,
                    bbox={"facecolor": "white", "edgecolor": "none", "alpha": 0.85})
        # Cada ponto tem o percentual oficial de rejeições.
        # Quando os testes coincidem, um único rótulo vale para os dois.
        # Para curvas distintas, deslocar Z para cima e exato para baixo,
        # com exceções nas extremidades de 0%/100%.
        min_x = float(group["effect_pp"].min())
        max_x = float(group["effect_pp"].max())
        for point in group.itertuples(index=False):
            x, z_y, b_y = float(point.effect_pp), float(point.z_rate), float(point.binomial_rate)
            horizontal = "left" if x == min_x else "right" if x == max_x else "center"
            box_style = {"facecolor": "white", "edgecolor": "none", "alpha": 0.9, "pad": 0.12}
            if math.isclose(z_y, b_y, rel_tol=0, abs_tol=1e-12):
                above = z_y <= 0.86
                ax.annotate(
                    pct(z_y), (x, z_y), xytext=(0, 8 if above else -12),
                    textcoords="offset points", ha=horizontal,
                    va="bottom" if above else "top",
                    fontsize=8.5, fontweight="bold", color=COLOR_OBS,
                    bbox=box_style, zorder=6,
                )
            else:
                above_z = z_y <= 0.85
                ax.annotate(
                    pct(z_y), (x, z_y), xytext=(0, 10 if above_z else -12),
                    textcoords="offset points", ha=horizontal,
                    va="bottom" if above_z else "top",
                    fontsize=8.5, fontweight="bold", color=COLOR_Z,
                    bbox=box_style, zorder=6,
                )
                above_b = b_y < 0.06
                ax.annotate(
                    pct(b_y), (x, b_y), xytext=(0, 5 if above_b else -9),
                    textcoords="offset points", ha=horizontal,
                    va="bottom" if above_b else "top",
                    fontsize=8.5, fontweight="bold", color=COLOR_BINOMIAL,
                    bbox=box_style, zorder=6,
                )
        ax.set_ylabel("Rejeições (%)")
        ax.set_yticks([0, .25, .50, .75, 1])
        ax.yaxis.set_major_formatter(PercentFormatter(1, decimals=0))
        ax.set_ylim(0, 1)
    axes[-1].set_xticks(effects, [str(e).removesuffix(".0").replace(".", ",") for e in effects])
    axes[-1].set_xlim(0, max(effects) * 1.03 or 1)
    axes[-1].set_xlabel("Efeito p − p₀ (p.p.)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, loc="outside lower center", ncols=2, frameon=False, fontsize=11)
    return fig
