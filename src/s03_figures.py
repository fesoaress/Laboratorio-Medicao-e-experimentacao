"""Figuras científicas estáticas, fontes e escalas explícitas (#69)."""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

from .s03_descriptive import CATEGORIES, METRICS
from .s03_inference import FACTORS, groups_for

COLORS = ("#b4637a", "#c8a653", "#377eb8", "#278575")


def save(fig, output, name):
    output.mkdir(parents=True, exist_ok=True)
    fig.text(.01, .006, "Fonte: coleta GitHub S02/S03; janela UTC [2025-10-01, 2026-10-01). Unidade: repositório.", fontsize=8)
    fig.tight_layout(rect=(0, .03, 1, 1))
    for extension in ("png", "svg", "pdf"):
        metadata = {"Creator": "Lab03 S03"}
        if extension == "pdf":
            metadata.update(CreationDate=None, ModDate=None)
        elif extension == "svg":
            metadata["Date"] = None
        fig.savefig(output / f"{name}.{extension}", dpi=170, metadata=metadata)
    plt.close(fig)


def run(data, descriptions, distribution, correlations, bootstrap, rework, output, sensitivity=None):
    plt.rcParams.update({"font.size": 10, "axes.spines.top": False, "axes.spines.right": False, "svg.hashsalt": "lab03-s03-v1"})
    fig, axes = plt.subplots(2, 3, figsize=(13, 8))
    for axis, (key, (field, unit, rq)) in zip(axes.flat, METRICS.items()):
        values = data[field].dropna().to_numpy(float)
        axis.hist(values, bins="auto", color=COLORS[2], edgecolor="white")
        if key not in ("cfr_a", "cfr_b") and len(values) and values.max() > max(np.median(values), .01) * 15:
            axis.clear()
            axis.hist(np.log1p(values), bins=20, color=COLORS[2], edgecolor="white")
            axis.set_xlabel(f"log(1 + valor em {unit})")
        else:
            axis.set_xlabel(unit)
        if key in ("cfr_a", "cfr_b"):
            axis.set_xlim(0, 1)
        axis.set_ylabel("Repositórios")
        axis.set_title(f"{rq} · {key}\nn={len(values)}; ausentes={len(data)-len(values)}")
    save(fig, output, "rq01_04_distributions")
    fig, axis = plt.subplots(figsize=(10, 5))
    labels = [*METRICS, "general"]
    bottom = np.zeros(len(labels))
    for cat, color in zip(CATEGORIES, COLORS):
        counts = [int(distribution.loc[(distribution.metric == key) & (distribution.category == cat), "n"].iloc[0]) for key in labels]
        axis.bar(labels, counts, bottom=bottom, label=cat, color=color)
        bottom += counts
    axis.set_ylabel("Repositórios com categoria calculável")
    axis.set_xticks(range(len(labels)), [f"{key}\nn={int(distribution.loc[distribution.metric == key, 'valid'].iloc[0])}" for key in labels])
    axis.legend(ncol=4)
    axis.set_title("DORA de referência; geral exige quatro métricas")
    save(fig, output, "dora_distribution")
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for axis, key in zip(axes, ("cfr_a", "cfr_b")):
        subset = data[[METRICS["df"][0], METRICS[key][0]]].dropna()
        row = correlations.loc[correlations.outcome == key].iloc[0]
        axis.scatter(subset.iloc[:, 0], subset.iloc[:, 1], alpha=.55, s=22, color=COLORS[2])
        axis.set_xscale("log")
        axis.set_xlabel("Releases estáveis / semana (log)")
        axis.set_ylabel(key + " (fração)")
        axis.set_title(f"RQ05 · n={row['n']}; rho={row['rho']:.3f}\np permutação={row['p_permutation']:.4g}")
    save(fig, output, "rq05_scatter")
    for factor in FACTORS:
        labels, cuts = groups_for(data[factor])
        fig, axes = plt.subplots(1, 4, figsize=(14, 4))
        for axis, key in zip(axes, ("df", "lt_release", "cfr_a", "recovery")):
            values = data[METRICS[key][0]].to_numpy(float)
            groups = [values[(labels == i) & np.isfinite(values)] for i in range(len(cuts) + 1)]
            axis.boxplot(groups, tick_labels=[f"G{i+1}\nn={len(g)}" for i, g in enumerate(groups)], showfliers=False)
            axis.set_title(key)
            axis.set_ylabel(METRICS[key][1])
            if key in ("df", "lt_release", "recovery"):
                axis.set_yscale("symlog", linthresh=1)
        fig.suptitle(f"RQ06 · {factor}; caixas Q1–Q3, linha mediana; outliers omitidos só na figura\nDF, LT e recuperação: escala symlog, região linear até 1", fontsize=10)
        save(fig, output, "rq06_" + factor)
    fig, axes = plt.subplots(1, len(bootstrap), figsize=(15, 4))
    for axis, (_, row) in zip(np.atleast_1d(axes), bootstrap.iterrows()):
        if np.isfinite(row.estimate):
            axis.plot([0, 0], [row.lower95, row.upper95], color=COLORS[2], linewidth=3)
            axis.scatter([0], [row.estimate], color=COLORS[3], zorder=3)
        axis.set_xticks([])
        axis.set_title(row.statistic.replace("median_", "mediana\n").replace("rho_", "rho\n") + f"\nn={int(row.n)}", fontsize=10)
        axis.set_ylabel("fração" if "cfr" in row.statistic and "rho" not in row.statistic else "rho" if "rho" in row.statistic else "releases/semana")
    fig.suptitle(f"Inovação · IC percentil 95%; {int(bootstrap.iterations.iloc[0])} reamostragens de repositórios, seed {int(bootstrap.seed.iloc[0])}")
    save(fig, output, "bootstrap_intervals")
    fig, axis = plt.subplots(figsize=(10, 5))
    ordered = rework.sort_values(["lower_bound", "upper_bound"])
    axis.vlines(np.arange(len(ordered)), ordered.lower_bound, ordered.upper_bound, color=COLORS[0], alpha=.6, label="Intervalo por classificações ausentes")
    axis.scatter(np.arange(len(ordered)), ordered.lower_bound, s=9, color=COLORS[2], label="Corretivas conhecidas / total")
    axis.set(xlabel="Repositórios ordenados por taxa", ylabel="Proporção de releases corretivas", title=f"RQ08 · n={len(rework)}; {rework.rework_rate.notna().sum()} taxas completas; intervalo de identificabilidade")
    axis.legend(fontsize=8)
    save(fig, output, "rq08_rework")
    if sensitivity is not None:
        fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
        for axis, (left, right) in zip(axes, (("C1", "C2"), ("C1", "C3"), ("C2", "C3"))):
            table = np.zeros((4, 4), dtype=int)
            for a, b in zip(sensitivity[f"{left}_general"], sensitivity[f"{right}_general"]):
                if a in CATEGORIES and b in CATEGORIES:
                    table[CATEGORIES.index(a), CATEGORIES.index(b)] += 1
            axis.imshow(table, cmap="Blues")
            for i in range(4):
                for j in range(4):
                    axis.text(j, i, str(table[i, j]), ha="center", va="center", color="white" if table[i, j] > table.max()/2 else "black")
            axis.set_xticks(range(4), CATEGORIES, rotation=25)
            axis.set_yticks(range(4), CATEGORIES)
            axis.set(xlabel=right, ylabel=left, title=f"RQ07 · n pareado={table.sum()}")
        save(fig, output, "rq07_transitions")
