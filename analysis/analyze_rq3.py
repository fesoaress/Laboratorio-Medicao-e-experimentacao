"""Gera a RQ3 usando a mesma elegibilidade auditada de RQ1/RQ2."""

from __future__ import annotations

import argparse
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

from lab02.analysis.analyze_rq1_rq2 import (
    COLORS,
    FIGURES_DIR,
    RESULTS_DIR,
    load_and_audit,
    require,
)
from lab02.metrics.run_metrics import DEFAULT_RESULTS_DIR
from lab02.trials.config import TRIALS_CSV


METRICS_CSV = DEFAULT_RESULTS_DIR / "metrics.csv"
METRIC_COLUMNS = {
    "trial_id",
    "participant",
    "kata",
    "treatment",
    "issue",
    "loc",
    "avg_cyclomatic_complexity",
    "duplication_percentage",
    "analysis_error",
    "solution_path",
    "source_kind",
}
METRICS = (
    ("loc", "LOC lógico (lloc)", "rq3_loc_ia_vs_manual.png"),
    (
        "avg_cyclomatic_complexity",
        "Complexidade ciclomática média por função/método",
        "rq3_complexidade_ia_vs_manual.png",
    ),
    (
        "duplication_percentage",
        "Linhas duplicadas (%)",
        "rq3_duplicacao_ia_vs_manual.png",
    ),
)

# Decisão explícita do grupo para a consolidação da RQ3: os quatro registros
# existentes de Islayder entram no recorte oficial desta pergunta de pesquisa.
# A proveniência original permanece nos CSVs e na tabela detalhada.
ISLAYDER_OFFICIAL_RQ3_TRIAL_IDS = frozenset(
    {"SIM-S02-I21", "SIM-S02-I24", "SIM-S02-I25", "SIM-S02-I26"}
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Analisa LOC, CC e duplicação da RQ3.")
    parser.add_argument("--output-dir", type=Path, default=RESULTS_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument(
        "--require-fernanda",
        action="store_true",
        help="Falha enquanto os quatro trials oficiais de Fernanda não estiverem completos.",
    )
    return parser.parse_args(argv)


def load_detail(require_fernanda: bool = False) -> pd.DataFrame:
    _, eligible_trials, _ = load_and_audit()
    fernanda = eligible_trials.loc[eligible_trials.participante == "Fernanda"]
    if require_fernanda:
        require(
            len(fernanda) == 4
            and fernanda.kata.nunique() == 4
            and fernanda.tratamento.value_counts().to_dict()
            == {"IA": 2, "Manual": 2},
            "os quatro trials oficiais de Fernanda ainda não estão completos",
        )

    raw_trials = pd.read_csv(
        TRIALS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    islayder = raw_trials.loc[
        raw_trials.trial_id.isin(ISLAYDER_OFFICIAL_RQ3_TRIAL_IDS)
    ].copy()
    require(
        set(islayder.trial_id) == set(ISLAYDER_OFFICIAL_RQ3_TRIAL_IDS),
        "os quatro registros oficiais de Islayder para RQ3 não estão completos",
    )
    require(
        len(islayder) == 4
        and islayder.participante.eq("Islayder").all()
        and islayder.kata.nunique() == 4
        and islayder.tratamento.value_counts().to_dict()
        == {"IA": 2, "Manual": 2},
        "os registros de Islayder não respeitam o desenho 2 IA + 2 Manual",
    )
    trials = pd.concat(
        [
            eligible_trials.loc[
                ~eligible_trials.trial_id.isin(ISLAYDER_OFFICIAL_RQ3_TRIAL_IDS)
            ],
            islayder,
        ],
        ignore_index=True,
    )

    metrics = pd.read_csv(
        METRICS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    require(METRIC_COLUMNS <= set(metrics), "metrics.csv: colunas obrigatórias ausentes")
    require(not metrics.trial_id.duplicated().any(), "trial_id duplicado em metrics.csv")

    selected = metrics.loc[metrics.trial_id.isin(trials.trial_id)].copy()
    missing = sorted(set(trials.trial_id) - set(selected.trial_id))
    require(not missing, f"trials elegíveis sem métricas RQ3: {', '.join(missing)}")
    require(len(selected) == len(trials), "quantidade de métricas não corresponde aos trials")

    trial_lookup = trials.set_index("trial_id")
    for _, metric in selected.iterrows():
        trial = trial_lookup.loc[metric.trial_id]
        require(metric.participant == trial.participante,
                f"{metric.trial_id}: participante diverge em metrics.csv")
        require(metric.kata == trial.kata,
                f"{metric.trial_id}: kata diverge em metrics.csv")
        require(metric.treatment == trial.tratamento,
                f"{metric.trial_id}: tratamento diverge em metrics.csv")
        require(metric.issue == trial.issue,
                f"{metric.trial_id}: Issue diverge em metrics.csv")
        require(metric.source_kind == trial.source_kind,
                f"{metric.trial_id}: origem diverge em metrics.csv")

    selected = selected.rename(
        columns={"participant": "participante", "treatment": "tratamento"}
    )
    for column, _, _ in METRICS:
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    selected["metricas_completas"] = selected[[item[0] for item in METRICS]].notna().all(axis=1)
    return selected[
        [
            "trial_id",
            "issue",
            "participante",
            "kata",
            "tratamento",
            "loc",
            "avg_cyclomatic_complexity",
            "duplication_percentage",
            "analysis_error",
            "metricas_completas",
            "solution_path",
            "source_kind",
        ]
    ].sort_values(["participante", "kata"])


def summarize(detail: pd.DataFrame, scope: str) -> pd.DataFrame:
    data = detail if scope == "grupo" else detail.loc[detail.participante == "Fernanda"]
    rows = []
    for treatment in ("IA", "Manual"):
        group = data.loc[data.tratamento == treatment]
        for column, label, _ in METRICS:
            values = group[column].dropna()
            q1 = values.quantile(0.25) if not values.empty else None
            q3 = values.quantile(0.75) if not values.empty else None
            rows.append(
                {
                    "escopo": scope,
                    "tratamento": treatment,
                    "metrica": column,
                    "unidade": label,
                    "n": len(values),
                    "mediana": values.median() if not values.empty else None,
                    "q1": q1,
                    "q3": q3,
                    "iqr": q3 - q1 if q1 is not None and q3 is not None else None,
                }
            )
    return pd.DataFrame(rows)


def make_loc_strip_plot(detail: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(9, 5.4))
    for x, treatment in enumerate(("Manual", "IA")):
        group = detail.loc[detail.tratamento == treatment].sort_values(
            ["participante", "kata"]
        )
        offsets = [
            (index - (len(group) - 1) / 2) * 0.095 for index in range(len(group))
        ]
        for offset, (_, row) in zip(offsets, group.iterrows()):
            ax.scatter(
                x + offset,
                row["loc"],
                color=COLORS[treatment],
                edgecolor="white",
                linewidth=0.8,
                s=72,
                zorder=3,
            )
            ax.annotate(
                f"{int(row['loc'])}",
                (x + offset, row["loc"]),
                xytext=(0, 7),
                textcoords="offset points",
                ha="center",
                fontsize=8,
            )
        median = group["loc"].median()
        ax.hlines(
            median,
            x - 0.31,
            x + 0.31,
            color=COLORS[treatment],
            linewidth=2.2,
            label=f"Mediana {treatment}: {median:.1f}",
            zorder=2,
        )
    ax.set(
        xlim=(-0.55, 1.55),
        xticks=[0, 1],
        xticklabels=["Manual", "IA"],
        ylabel="Linhas de código (LOC)",
        title="LOC por tratamento",
    )
    ax.grid(axis="y", alpha=0.22)
    ax.margins(y=0.14)
    ax.legend(loc="best", frameon=True)
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)


def make_complexity_slope_chart(detail: pd.DataFrame, output: Path) -> None:
    paired = (
        detail.groupby(["participante", "tratamento"])[
            "avg_cyclomatic_complexity"
        ]
        .median()
        .unstack()
    )
    require(
        {"Manual", "IA"} <= set(paired.columns),
        "slope chart exige os dois tratamentos por participante",
    )
    require(
        paired[["Manual", "IA"]].notna().all(axis=None),
        "slope chart encontrou participante sem um dos tratamentos",
    )

    participant_colors = {
        participant: color
        for participant, color in zip(
            sorted(paired.index), ("#4c78a8", "#59a14f", "#b279a2")
        )
    }
    ordered_participants = list(paired.sort_index().index)
    participant_offsets = {
        participant: (index - (len(ordered_participants) - 1) / 2) * 0.09
        for index, participant in enumerate(ordered_participants)
    }

    fig, ax = plt.subplots(figsize=(9.4, 6.0))
    for participant, row in paired.sort_index().iterrows():
        values = [row["Manual"], row["IA"]]
        color = participant_colors[participant]
        offset = participant_offsets[participant]
        endpoint_x = [offset, 1 + offset]
        ax.plot(
            endpoint_x,
            values,
            color=color,
            linewidth=2,
            marker="o",
            markersize=7,
            zorder=3,
        )

        for treatment, x in zip(("Manual", "IA"), endpoint_x):
            trials = detail.loc[
                (detail.participante == participant)
                & (detail.tratamento == treatment)
            ].sort_values("kata")
            trial_offsets = (-0.016, 0.016)
            for trial_offset, (_, trial) in zip(trial_offsets, trials.iterrows()):
                trial_x = x + trial_offset
                trial_value = trial.avg_cyclomatic_complexity
                ax.scatter(
                    trial_x,
                    trial_value,
                    facecolor="white",
                    edgecolor=color,
                    linewidth=1.4,
                    s=42,
                    zorder=4,
                )
                ax.annotate(
                    f"K{trial.kata[4]}",
                    (trial_x, trial_value),
                    xytext=(0, 6),
                    textcoords="offset points",
                    ha="center",
                    fontsize=7,
                    color=color,
                )

        ax.annotate(
            f"{participant} · {values[1]:.2f}",
            (endpoint_x[1], values[1]),
            xytext=(9, 0),
            textcoords="offset points",
            ha="left",
            va="center",
            fontsize=8,
        )
    ax.set(
        xlim=(-0.25, 1.42),
        xticks=[0, 1],
        xticklabels=["Manual", "IA"],
        ylabel="Complexidade ciclomática média por função/método",
        title="Variação da complexidade ciclomática entre os tratamentos",
    )
    ax.grid(axis="y", alpha=0.22)
    ax.margins(y=0.12)
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                color="#666666",
                marker="o",
                linewidth=2,
                label="Mediana dos dois katas",
            ),
            Line2D(
                [0],
                [0],
                color="#666666",
                marker="o",
                markerfacecolor="white",
                linewidth=0,
                label="Kata individual",
            ),
        ],
        loc="upper left",
    )
    fig.text(
        0.5,
        0.015,
        "Linhas comparam medianas por participante; círculos vazios mostram os dois katas que formam cada mediana.",
        ha="center",
        fontsize=8,
        color="#555555",
    )
    fig.tight_layout(rect=(0, 0.05, 1, 1))
    fig.savefig(output)
    plt.close(fig)


def make_duplication_lollipop(detail: pd.DataFrame, output: Path) -> None:
    data = detail.copy()
    data["ordem_tratamento"] = pd.Categorical(
        data.tratamento, categories=["Manual", "IA"], ordered=True
    )
    data = data.sort_values(["ordem_tratamento", "participante", "kata"])
    labels = [
        f"{row.participante} · K{row.kata[4]} · {row.tratamento}"
        for _, row in data.iterrows()
    ]
    positions = list(range(len(data)))

    fig, ax = plt.subplots(figsize=(9, 6.4))
    for position, (_, row) in zip(positions, data.iterrows()):
        value = row.duplication_percentage
        color = COLORS[row.tratamento]
        ax.hlines(position, 0, value, color=color, linewidth=2, alpha=0.8)
        ax.scatter(value, position, color=color, s=66, zorder=3)
        ax.annotate(
            f"{value:.1f}%",
            (value, position),
            xytext=(7, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )

    maximum = max(float(data.duplication_percentage.max()), 1.0)
    ax.axvline(0, color="#777777", linewidth=0.8)
    ax.set(
        xlim=(-maximum * 0.05, maximum * 1.18),
        yticks=positions,
        yticklabels=labels,
        xlabel="Código duplicado (%)",
        title="Duplicação de código por tratamento",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.22)
    ax.legend(
        handles=[
            Line2D([0], [0], marker="o", color=COLORS[treatment],
                   linewidth=2, label=treatment)
            for treatment in ("Manual", "IA")
        ],
        loc="lower right",
    )
    fig.tight_layout()
    fig.savefig(output)
    plt.close(fig)


def make_figures(detail: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "figure.dpi": 140})
    make_loc_strip_plot(detail, figures_dir / "rq3_loc_ia_vs_manual.png")
    make_complexity_slope_chart(
        detail, figures_dir / "rq3_complexidade_ia_vs_manual.png"
    )
    make_duplication_lollipop(
        detail, figures_dir / "rq3_duplicacao_ia_vs_manual.png"
    )


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        detail = load_detail(require_fernanda=args.require_fernanda)
    except ValueError as exc:
        print(f"RQ3 não executada: {exc}")
        return 2
    summary = pd.concat(
        [summarize(detail, "grupo"), summarize(detail, "Fernanda")],
        ignore_index=True,
    )
    args.output_dir.mkdir(parents=True, exist_ok=True)
    detail.to_csv(args.output_dir / "rq3_detalhe.csv", index=False, encoding="utf-8")
    summary.to_csv(args.output_dir / "rq3_resumo.csv", index=False, encoding="utf-8")
    make_figures(detail, args.figures_dir)
    print(f"Trials RQ3 elegíveis: {len(detail)}")
    print(summary.to_string(index=False))
    print(f"Tabelas: {args.output_dir}; gráficos: {args.figures_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
