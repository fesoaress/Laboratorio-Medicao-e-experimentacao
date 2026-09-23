"""Gera o dashboard final de RQ1, RQ2, RQ3 e inovação.

Execute da raiz: python -m lab02.dashboard.build_dashboard

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
from matplotlib.lines import Line2D
import pandas as pd

from lab02.analysis.analyze_rq1_rq2 import COLORS, FIGURES_DIR, RESULTS_DIR


OUTPUT_PATH = FIGURES_DIR / "dashboard_final.png"
RQ1_CSV = RESULTS_DIR / "rq1_resumo.csv"
RQ1_DETAIL_CSV = RESULTS_DIR / "rq1_detalhe.csv"
RQ2_CSV = RESULTS_DIR / "rq2_resumo.csv"
INNOVATION_CSV = RESULTS_DIR / "inovacao_resumo.csv"
INNOVATION_DETAIL_CSV = RESULTS_DIR / "inovacao_detalhe.csv"
RQ3_DETAIL_CSV = RESULTS_DIR / "rq3_detalhe.csv"
RQ3_SUMMARY_CSV = RESULTS_DIR / "rq3_resumo.csv"
TREATMENTS = ("IA", "Manual")


def load_tables() -> dict[str, pd.DataFrame]:
    return {
        "rq1": pd.read_csv(RQ1_CSV),
        "rq1_detail": pd.read_csv(RQ1_DETAIL_CSV),
        "rq2": pd.read_csv(RQ2_CSV),
        "inovacao": pd.read_csv(INNOVATION_CSV),
        "inovacao_detail": pd.read_csv(INNOVATION_DETAIL_CSV),
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
        f"RQ3: n={len(rq3_detail)} artefatos · observed={counts.get('observed', 0)} · "
        f"agent_delegated_codex_work={counts.get('agent_delegated_codex_work', 0)} · "
        f"participantes: {', '.join(participants)} · SIM-* excluídos."
    )


def _kpi(ax, value: str, label: str, color: str = "#3333B2") -> None:
    ax.set_facecolor("#F4F4FB")
    for spine in ax.spines.values():
        spine.set_color("#D3D3EE")
        spine.set_linewidth(0.9)
    ax.set_xticks([])
    ax.set_yticks([])
    ax.text(
        0.5,
        0.62,
        value,
        ha="center",
        va="center",
        fontsize=15,
        fontweight="bold",
        color=color,
    )
    ax.text(
        0.5,
        0.25,
        label,
        ha="center",
        va="center",
        fontsize=8,
        color="#4b5563",
    )


def _compact_box(ax, frame: pd.DataFrame, column: str, title: str, ylabel: str) -> None:
    values = [
        frame.loc[frame.tratamento == treatment, column] for treatment in TREATMENTS
    ]
    boxes = ax.boxplot(
        values,
        tick_labels=TREATMENTS,
        patch_artist=True,
        widths=0.5,
        showfliers=False,
        medianprops={"color": "#202124", "linewidth": 1.8},
    )
    for patch, treatment in zip(boxes["boxes"], TREATMENTS):
        patch.set_facecolor(COLORS[treatment])
        patch.set_alpha(0.22)
        patch.set_edgecolor(COLORS[treatment])
    for position, treatment in enumerate(TREATMENTS, start=1):
        group = frame.loc[frame.tratamento == treatment].sort_values(
            ["participante", "kata"]
        )
        offsets = [
            (index - (len(group) - 1) / 2) * 0.045
            for index in range(len(group))
        ]
        ax.scatter(
            [position + offset for offset in offsets],
            group[column],
            color=COLORS[treatment],
            edgecolor="white",
            linewidth=0.6,
            s=29,
            zorder=3,
        )
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(ylabel, fontsize=8)
    ax.grid(axis="y", alpha=0.18)


def build_dashboard(tables: dict[str, pd.DataFrame]) -> None:
    plt.rcParams.update(
        {
            "font.size": 9,
            "figure.dpi": 150,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlecolor": "#3333B2",
            "axes.edgecolor": "#6b7280",
        }
    )
    rq1 = tables["rq1"].set_index("tratamento").loc[list(TREATMENTS)]
    rq1_detail = tables["rq1_detail"]
    rq2 = tables["rq2"].set_index("tratamento").loc[list(TREATMENTS)]
    innovation = tables["inovacao"].set_index("tratamento").loc[list(TREATMENTS)]
    innovation_detail = tables["inovacao_detail"]
    rq3_detail = tables["rq3_detail"]
    final_rq3_summary(tables["rq3_summary"], rq3_detail)

    fig = plt.figure(figsize=(16, 10), facecolor="white")
    grid = fig.add_gridspec(
        3,
        6,
        height_ratios=[0.85, 2.7, 2.8],
        hspace=0.58,
        wspace=0.72,
    )
    kpi_grid = grid[0, :].subgridspec(2, 4, hspace=0.18, wspace=0.15)
    kpis = [
        ("12", "trials finais", "#3333B2"),
        ("3", "participantes", "#3333B2"),
        ("6", "trials IA", COLORS["IA"]),
        ("6", "trials Manual", COLORS["Manual"]),
        (
            f"{rq1.loc['IA', 'mediana_segundos']:.2f} s".replace(".", ","),
            "mediana IA",
            COLORS["IA"],
        ),
        (
            f"{rq1.loc['Manual', 'mediana_segundos']:.2f} s".replace(".", ","),
            "mediana Manual",
            COLORS["Manual"],
        ),
        ("105/105", "testes finais passando", "#3333B2"),
        ("0%", "duplicação detectada", "#5f6368"),
    ]
    for index, (value, label, color) in enumerate(kpis):
        _kpi(fig.add_subplot(kpi_grid[index // 4, index % 4]), value, label, color)

    time_ax = fig.add_subplot(grid[1, 0:2])
    _compact_box(
        time_ax,
        rq1_detail,
        "tempo_segundos",
        "RQ1 — tempo até green",
        "Segundos",
    )

    tests_ax = fig.add_subplot(grid[1, 2:4])
    y = [1, 0]
    for y_pos, treatment in zip(y, TREATMENTS):
        passed = int(rq2.loc[treatment, "passed_soma"])
        total = int(rq2.loc[treatment, "total_testes_soma"])
        tests_ax.barh(y_pos, 100, color="#e5e7eb", height=0.42)
        tests_ax.barh(y_pos, 100 * passed / total, color=COLORS[treatment], height=0.42)
        tests_ax.text(
            101.5,
            y_pos,
            f"{passed}/{total}",
            va="center",
            fontsize=9,
            fontweight="bold",
        )
    tests_ax.set(
        yticks=y,
        yticklabels=TREATMENTS,
        xlim=(0, 116),
        xlabel="Aprovação final (%)",
        title="RQ2 — testes finais",
    )
    tests_ax.grid(axis="x", alpha=0.18)

    cycles_ax = fig.add_subplot(grid[1, 4:6])
    for y_pos, treatment in zip((1, 0), TREATMENTS):
        group = innovation_detail.loc[
            innovation_detail.tratamento == treatment
        ].sort_values(["participante", "kata"])
        offsets = [
            (index - (len(group) - 1) / 2) * 0.055
            for index in range(len(group))
        ]
        cycles_ax.scatter(
            group.ciclo_ate_green,
            [y_pos + offset for offset in offsets],
            color=COLORS[treatment],
            edgecolor="white",
            linewidth=0.6,
            s=46,
            zorder=3,
        )
        cycles_ax.vlines(
            float(innovation.loc[treatment, "ciclos_mediana"]),
            y_pos - 0.22,
            y_pos + 0.22,
            color="#202124",
            linewidth=2,
        )
    cycles_ax.set(
        yticks=[1, 0],
        yticklabels=TREATMENTS,
        xticks=[1, 2],
        xlim=(0.75, 2.25),
        xlabel="Ciclo até green",
        title="Inovação — retrabalho",
    )
    cycles_ax.grid(axis="x", alpha=0.18)

    loc_ax = fig.add_subplot(grid[2, 0:2])
    _compact_box(loc_ax, rq3_detail, "loc", "RQ3 — LOC lógico", "lloc")

    cc_ax = fig.add_subplot(grid[2, 2:4])
    _compact_box(
        cc_ax,
        rq3_detail,
        "avg_cyclomatic_complexity",
        "RQ3 — complexidade média",
        "CC por função/método",
    )

    scatter_ax = fig.add_subplot(grid[2, 4:6])
    participant_markers = {"Fernanda": "o", "Islayder": "s", "Vinicius": "^"}
    for _, row in rq3_detail.iterrows():
        scatter_ax.scatter(
            row["loc"],
            row.avg_cyclomatic_complexity,
            color=COLORS[row.tratamento],
            marker=participant_markers[row.participante],
            edgecolor="white",
            linewidth=0.6,
            s=47,
        )
    scatter_ax.set(
        xlabel="LOC lógico",
        ylabel="CC média",
        title="RQ3 — LOC × complexidade",
    )
    scatter_ax.grid(alpha=0.18)
    scatter_ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color="none",
                markerfacecolor=COLORS[treatment],
                markeredgecolor="white",
                label=treatment,
            )
            for treatment in TREATMENTS
        ],
        frameon=False,
        loc="upper right",
    )

    fig.suptitle(
        "Lab02 — Assistentes de IA versus codificação Manual",
        fontsize=16,
        fontweight="bold",
        color="#3333B2",
        y=0.99,
    )
    fig.text(
        0.5,
        0.012,
        data_composition_note(rq3_detail),
        ha="center",
        fontsize=7.5,
        color="#5f6368",
    )
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUTPUT_PATH, dpi=200, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def main() -> None:
    tables = load_tables()
    build_dashboard(tables)
    print(f"Dashboard salvo em: {OUTPUT_PATH}")
    print(data_composition_note(tables["rq3_detail"]))


if __name__ == "__main__":
    main()
