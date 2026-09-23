"""Consolida RQ1, RQ2, RQ3 e inovação num único painel.

Execute da raiz: python -m lab02.dashboard.build_dashboard

Fontes:
  - lab02/analysis/results/rq1_resumo.csv
  - lab02/analysis/results/rq2_resumo.csv
  - lab02/analysis/results/inovacao_resumo.csv
  - lab02/analysis/results/rq3_resumo.csv
  - lab02/analysis/results/rq3_detalhe.csv

Saída: reports/figures/dashboard_final.png
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lab02-s03-mpl-cache")
)
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from lab02.analysis.analyze_rq1_rq2 import COLORS, FIGURES_DIR, RESULTS_DIR


OUTPUT_PATH = FIGURES_DIR / "dashboard_final.png"
RQ1_CSV = RESULTS_DIR / "rq1_resumo.csv"
RQ2_CSV = RESULTS_DIR / "rq2_resumo.csv"
INOVACAO_CSV = RESULTS_DIR / "inovacao_resumo.csv"
RQ3_DETAIL_CSV = RESULTS_DIR / "rq3_detalhe.csv"
RQ3_SUMMARY_CSV = RESULTS_DIR / "rq3_resumo.csv"
TREATMENTS = ("IA", "Manual")


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "rq1": pd.read_csv(RQ1_CSV),
        "rq2": pd.read_csv(RQ2_CSV),
        "inovacao": pd.read_csv(INOVACAO_CSV),
        "rq3_detail": pd.read_csv(RQ3_DETAIL_CSV),
        "rq3_summary": pd.read_csv(RQ3_SUMMARY_CSV),
    }


def final_rq3_summary(
    rq3_summary: pd.DataFrame, rq3_detail: pd.DataFrame
) -> pd.DataFrame:
    """Valida e devolve o resumo final de grupo produzido por analyze_rq3."""
    if len(rq3_detail) != 12:
        raise ValueError(f"RQ3 final exige 12 artefatos; encontrados={len(rq3_detail)}")
    if rq3_detail.trial_id.str.startswith("SIM-").any():
        raise ValueError("RQ3 final contém ID SIM-*")
    allowed = {"observed", "agent_delegated_codex_work"}
    if not rq3_detail.source_kind.isin(allowed).all():
        raise ValueError("RQ3 final contém proveniência não autorizada")
    if set(rq3_detail.participante) != {"Fernanda", "Islayder", "Vinicius"}:
        raise ValueError("RQ3 final não contém os três participantes")

    group = rq3_summary.loc[rq3_summary.escopo == "grupo"].copy()
    expected_metrics = {
        "loc",
        "avg_cyclomatic_complexity",
        "duplication_percentage",
    }
    if (
        len(group) != 6
        or set(group.metrica) != expected_metrics
        or set(group.tratamento) != set(TREATMENTS)
        or not group.n.eq(6).all()
    ):
        raise ValueError("rq3_resumo.csv não representa 6 artefatos por tratamento")
    return group


def data_composition_note(rq3_detail: pd.DataFrame) -> str:
    counts = rq3_detail.source_kind.value_counts().to_dict()
    participants = sorted(rq3_detail.participante.unique())
    return (
        f"RQ3 final: n={len(rq3_detail)} artefatos mensurados · "
        f"observed={counts.get('observed', 0)} · "
        f"agent_delegated_codex_work={counts.get('agent_delegated_codex_work', 0)}. "
        f"Participantes: {', '.join(participants)}. "
        "Cenários SIM-* não integram as tabelas finais."
    )


def bar_with_labels(
    ax,
    values: dict[str, float],
    ylabel: str,
    title: str,
    fmt: str = "{:.2f}",
) -> None:
    treatments = list(values.keys())
    heights = list(values.values())
    colors = [COLORS[treatment] for treatment in treatments]
    bars = ax.bar(treatments, heights, color=colors, width=0.55)
    for bar, height in zip(bars, heights):
        ax.annotate(
            fmt.format(height),
            (bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 4),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )
    ax.set_ylabel(ylabel)
    ax.set_title(title, fontsize=10)
    ax.grid(axis="y", alpha=0.25)


def build_dashboard(tables: dict[str, pd.DataFrame]) -> None:
    plt.rcParams.update({"font.size": 9, "figure.dpi": 150})
    rq1 = tables["rq1"]
    rq2 = tables["rq2"]
    innovation = tables["inovacao"]
    rq3_summary = final_rq3_summary(
        tables["rq3_summary"], tables["rq3_detail"]
    )

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    time_values = {row.tratamento: row.mediana_min for row in rq1.itertuples()}
    bar_with_labels(
        axes[0, 0], time_values, "Minutos (mediana)", "RQ1 — Tempo até green", "{:.2f} min"
    )

    success = {
        row.tratamento: row.taxa_final_mediana_pct for row in rq2.itertuples()
    }
    bar_with_labels(
        axes[0, 1], success, "Testes passando (%)", "RQ2 — Taxa final de sucesso", "{:.1f}%"
    )
    axes[0, 1].set_ylim(0, 110)

    cycles = {row.tratamento: row.ciclos_mediana for row in innovation.itertuples()}
    bar_with_labels(
        axes[0, 2], cycles, "Ciclos (mediana)", "Inovação — Ciclos até green", "{:.1f}"
    )

    loc = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[rq3_summary.metrica == "loc"].itertuples()
    }
    bar_with_labels(axes[1, 0], loc, "LOC (mediana)", "RQ3 — LOC lógico", "{:.1f}")

    complexity = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[
            rq3_summary.metrica == "avg_cyclomatic_complexity"
        ].itertuples()
    }
    bar_with_labels(
        axes[1, 1],
        complexity,
        "CC média (mediana)",
        "RQ3 — Complexidade ciclomática",
        "{:.2f}",
    )

    duplication = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[
            rq3_summary.metrica == "duplication_percentage"
        ].itertuples()
    }
    bar_with_labels(
        axes[1, 2],
        duplication,
        "Duplicação % (mediana)",
        "RQ3 — Duplicação de código",
        "{:.1f}%",
    )
    axes[1, 2].set_ylim(0, max(1.0, max(duplication.values()) * 1.3))

    participants = sorted(tables["rq3_detail"].participante.unique())
    fig.suptitle(
        "Lab02 — Dashboard consolidado (Sprint 03)\n"
        f"RQ1/RQ2: 12 trials · RQ3: {len(tables['rq3_detail'])} artefatos · "
        f"participantes: {', '.join(participants)}",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.01,
        data_composition_note(tables["rq3_detail"]),
        ha="center",
        fontsize=7.5,
        wrap=True,
        color="#444444",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.94))
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH)
    plt.close(fig)


def main() -> None:
    tables = load_tables()
    build_dashboard(tables)
    print(f"Dashboard salvo em: {OUTPUT_PATH}")
    print(data_composition_note(tables["rq3_detail"]))


if __name__ == "__main__":
    main()
