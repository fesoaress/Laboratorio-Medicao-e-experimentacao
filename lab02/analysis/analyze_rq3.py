"""Gera a RQ3 a partir dos trials finais e dos artefatos rastreáveis."""

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
    require,
)
from lab02.metrics.run_metrics import DEFAULT_RESULTS_DIR
from lab02.trials.config import BASE_DIR, TRIALS_CSV


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
    "cyclomatic_complexity_max",
    "duplicated_lines",
    "duplicated_blocks",
    "analyzed_functions",
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

ISLAYDER_RQ3_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "trials"
    / "results"
    / "rq3_artifacts"
    / "islayder"
    / "manifest.csv"
)
FERNANDA_RQ3_MANIFEST = (
    Path(__file__).resolve().parents[1]
    / "trials"
    / "results"
    / "rq3_artifacts"
    / "fernanda"
    / "manifest.csv"
)
FINAL_SOURCE_KINDS = frozenset({"observed", "agent_delegated_codex_work"})
FINAL_PARTICIPANTS = frozenset({"Fernanda", "Islayder", "Vinicius"})


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


def load_manifest(
    path: Path, participant: str, default_source_kind: str | None = None
) -> pd.DataFrame:
    require(path.is_file(), f"manifesto RQ3 de {participant} ausente")
    manifest = pd.read_csv(
        path, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    required = {
        "trial_id",
        "participant",
        "issue",
        "kata",
        "treatment",
        "solution_path",
        "test_path",
    }
    require(required <= set(manifest), f"manifesto de {participant}: colunas ausentes")
    if "source_kind" not in manifest:
        require(default_source_kind is not None, f"manifesto de {participant}: origem ausente")
        manifest["source_kind"] = default_source_kind
    require(
        len(manifest) == 4
        and manifest.participant.eq(participant).all()
        and manifest.kata.nunique() == 4
        and manifest.treatment.value_counts().to_dict() == {"IA": 2, "Manual": 2},
        f"manifesto de {participant} não respeita o desenho 2 IA + 2 Manual",
    )
    require(
        not manifest.trial_id.str.startswith("SIM-").any()
        and manifest.source_kind.isin(FINAL_SOURCE_KINDS).all(),
        f"manifesto final de {participant} contém origem ou ID inválido",
    )
    for row in manifest.itertuples(index=False):
        require(
            (BASE_DIR / row.solution_path).is_file(),
            f"código RQ3 ausente: {row.solution_path}",
        )
        require(
            (BASE_DIR / row.test_path).is_file(),
            f"teste RQ3 ausente: {row.test_path}",
        )
    return manifest


def load_detail(require_fernanda: bool = False) -> pd.DataFrame:
    raw_trials = pd.read_csv(
        TRIALS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    required_trial_columns = {
        "trial_id",
        "issue",
        "participante",
        "kata",
        "tratamento",
        "status",
        "codigo_path",
        "source_kind",
    }
    require(
        required_trial_columns <= set(raw_trials),
        "trials.csv: colunas obrigatórias ausentes para validar RQ3",
    )

    islayder_manifest = load_manifest(
        ISLAYDER_RQ3_MANIFEST, "Islayder", default_source_kind="observed"
    )
    fernanda_manifest = load_manifest(FERNANDA_RQ3_MANIFEST, "Fernanda")
    for row in fernanda_manifest.itertuples(index=False):
        raw = raw_trials.loc[raw_trials.trial_id == row.trial_id]
        require(len(raw) == 1, f"{row.trial_id}: trial final de Fernanda ausente")
        trial = raw.iloc[0]
        require(
            trial.participante == row.participant
            and trial.issue == row.issue
            and trial.kata == row.kata
            and trial.tratamento == row.treatment
            and trial.source_kind == row.source_kind
            and trial.status == "green",
            f"{row.trial_id}: manifesto de Fernanda diverge de trials.csv",
        )

    base_trials = raw_trials.loc[
        raw_trials.participante.eq("Vinicius")
        & raw_trials.source_kind.isin(FINAL_SOURCE_KINDS)
        & raw_trials.status.eq("green")
    ].copy()
    base_trials = base_trials.rename(
        columns={
            "participante": "participant",
            "tratamento": "treatment",
            "codigo_path": "solution_path",
        }
    )
    expected = base_trials[
        [
            "trial_id",
            "participant",
            "issue",
            "kata",
            "treatment",
            "solution_path",
            "source_kind",
        ]
    ].copy()
    manifest_expected = pd.concat(
        [islayder_manifest, fernanda_manifest], ignore_index=True
    )[
        [
            "trial_id",
            "participant",
            "issue",
            "kata",
            "treatment",
            "solution_path",
            "source_kind",
        ]
    ].copy()
    expected = pd.concat([expected, manifest_expected], ignore_index=True)
    require(not expected.trial_id.duplicated().any(), "trial_id duplicado na seleção RQ3")

    metrics = pd.read_csv(
        METRICS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    require(METRIC_COLUMNS <= set(metrics), "metrics.csv: colunas obrigatórias ausentes")
    require(not metrics.trial_id.duplicated().any(), "trial_id duplicado em metrics.csv")

    selected = metrics.loc[metrics.trial_id.isin(expected.trial_id)].copy()
    missing = sorted(set(expected.trial_id) - set(selected.trial_id))
    require(not missing, f"trials elegíveis sem métricas RQ3: {', '.join(missing)}")
    require(
        len(selected) == len(expected),
        "quantidade de métricas não corresponde aos artefatos finais",
    )
    require(
        not selected.trial_id.str.startswith("SIM-").any()
        and selected.source_kind.isin(FINAL_SOURCE_KINDS).all(),
        "RQ3 final selecionou métrica simulada ou origem não autorizada",
    )

    trial_lookup = expected.set_index("trial_id")
    for _, metric in selected.iterrows():
        trial = trial_lookup.loc[metric.trial_id]
        require(metric.participant == trial.participant,
                f"{metric.trial_id}: participante diverge em metrics.csv")
        require(metric.kata == trial.kata,
                f"{metric.trial_id}: kata diverge em metrics.csv")
        require(metric.treatment == trial.treatment,
                f"{metric.trial_id}: tratamento diverge em metrics.csv")
        require(metric.issue == trial.issue,
                f"{metric.trial_id}: Issue diverge em metrics.csv")
        require(metric.source_kind == trial.source_kind,
                f"{metric.trial_id}: origem diverge em metrics.csv")
        require(metric.solution_path == trial.solution_path,
                f"{metric.trial_id}: caminho do código diverge em metrics.csv")

    for participant in FINAL_PARTICIPANTS:
        group = selected.loc[selected.participant == participant]
        require(
            len(group) == 4
            and group.kata.nunique() == 4
            and group.treatment.value_counts().to_dict() == {"IA": 2, "Manual": 2},
            f"{participant}: RQ3 final não respeita o desenho 2 IA + 2 Manual",
        )
    if require_fernanda:
        require(
            len(selected.loc[selected.participant == "Fernanda"]) == 4,
            "os quatro trials oficiais de Fernanda ainda não estão completos",
        )

    selected = selected.rename(
        columns={"participant": "participante", "treatment": "tratamento"}
    )
    numeric_columns = [item[0] for item in METRICS] + [
        "cyclomatic_complexity_max",
        "duplicated_lines",
        "duplicated_blocks",
        "analyzed_functions",
    ]
    for column in numeric_columns:
        selected[column] = pd.to_numeric(selected[column], errors="coerce")
    selected["metricas_completas"] = selected[numeric_columns].notna().all(axis=1)
    require(
        selected["metricas_completas"].all()
        and selected.analysis_error.eq("").all(),
        "RQ3 final contém métrica ausente ou erro de análise",
    )
    return selected[
        [
            "trial_id",
            "issue",
            "participante",
            "kata",
            "tratamento",
            "loc",
            "avg_cyclomatic_complexity",
            "cyclomatic_complexity_max",
            "duplication_percentage",
            "duplicated_lines",
            "duplicated_blocks",
            "analyzed_functions",
            "analysis_error",
            "metricas_completas",
            "solution_path",
            "source_kind",
        ]
    ].sort_values(["participante", "kata"])


def summarize(detail: pd.DataFrame, participant: str | None = None) -> pd.DataFrame:
    scope = "grupo" if participant is None else participant
    data = detail if participant is None else detail.loc[
        detail.participante == participant
    ]
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


def make_metric_boxplot(
    detail: pd.DataFrame,
    column: str,
    ylabel: str,
    title: str,
    output: Path,
    decimals: int,
) -> None:
    treatments = ("IA", "Manual")
    values = [
        detail.loc[detail.tratamento == treatment, column]
        for treatment in treatments
    ]
    fig, ax = plt.subplots(figsize=(8.5, 5.3))
    boxes = ax.boxplot(
        values,
        tick_labels=treatments,
        patch_artist=True,
        widths=0.48,
        showfliers=False,
        medianprops={"color": "#202124", "linewidth": 2.2},
        whiskerprops={"color": "#5f6368", "linewidth": 1.2},
        capprops={"color": "#5f6368", "linewidth": 1.2},
    )
    for patch, treatment in zip(boxes["boxes"], treatments):
        patch.set_facecolor(COLORS[treatment])
        patch.set_alpha(0.22)
        patch.set_edgecolor(COLORS[treatment])
        patch.set_linewidth(1.5)

    initials = {"Fernanda": "F", "Islayder": "I", "Vinicius": "V"}
    for position, treatment in enumerate(treatments, start=1):
        group = detail.loc[detail.tratamento == treatment].sort_values(
            ["participante", "kata"]
        )
        offsets = [
            (index - (len(group) - 1) / 2) * 0.055
            for index in range(len(group))
        ]
        for label_index, (offset, (_, row)) in enumerate(
            zip(offsets, group.iterrows())
        ):
            value = row[column]
            ax.scatter(
                position + offset,
                value,
                color=COLORS[treatment],
                edgecolor="white",
                linewidth=0.8,
                s=58,
                zorder=3,
            )
            ax.annotate(
                f"{initials[row.participante]}·K{row.kata[4]}",
                (position + offset, value),
                xytext=(0, 7 + 7 * (label_index % 2)),
                textcoords="offset points",
                ha="center",
                fontsize=7.5,
                color="#34373a",
            )
    ax.set(ylabel=ylabel, title=title)
    ax.grid(axis="y", alpha=0.22)
    ax.text(
        0.01,
        -0.16,
        "Caixa = Q1–Q3; linha = mediana; pontos = artefatos; rótulos: participante e kata.",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6368",
    )
    median_text = " · ".join(
        f"{treatment}: {detail.loc[detail.tratamento == treatment, column].median():.{decimals}f}"
        for treatment in treatments
    )
    ax.text(
        0.99,
        0.98,
        f"Medianas — {median_text}",
        transform=ax.transAxes,
        ha="right",
        va="top",
        fontsize=8.5,
        color="#34373a",
    )
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
    plt.close(fig)


def make_loc_complexity_scatter(detail: pd.DataFrame, output: Path) -> None:
    markers = {"Fernanda": "o", "Islayder": "s", "Vinicius": "^"}
    initials = {"Fernanda": "F", "Islayder": "I", "Vinicius": "V"}
    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    label_offsets = {
        ("Fernanda", "kata4_manutencao_preditiva"): (5, 7),
        ("Islayder", "kata4_manutencao_preditiva"): (5, -12),
        ("Vinicius", "kata4_manutencao_preditiva"): (5, 7),
    }
    for _, row in detail.sort_values(["tratamento", "participante", "kata"]).iterrows():
        ax.scatter(
            row["loc"],
            row.avg_cyclomatic_complexity,
            color=COLORS[row.tratamento],
            marker=markers[row.participante],
            edgecolor="white",
            linewidth=0.8,
            s=76,
            zorder=3,
        )
        ax.annotate(
            f"{initials[row.participante]}·K{row.kata[4]}",
            (row["loc"], row.avg_cyclomatic_complexity),
            xytext=label_offsets.get((row.participante, row.kata), (5, 5)),
            textcoords="offset points",
            fontsize=7.5,
        )
    legend_items = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="none",
            markerfacecolor=COLORS[treatment],
            markeredgecolor="white",
            markersize=8,
            label=treatment,
        )
        for treatment in ("IA", "Manual")
    ] + [
        Line2D(
            [0],
            [0],
            marker=markers[participant],
            color="#5f6368",
            linewidth=0,
            markerfacecolor="white",
            markersize=7,
            label=participant,
        )
        for participant in ("Fernanda", "Islayder", "Vinicius")
    ]
    ax.set(
        xlabel="LOC lógico (lloc)",
        ylabel="Complexidade ciclomática média",
        title="RQ3 — relação exploratória entre LOC e complexidade",
    )
    ax.grid(alpha=0.22)
    ax.legend(handles=legend_items, frameon=False, ncol=2, loc="upper right")
    ax.text(
        0.01,
        -0.16,
        "Cada ponto é um artefato; o gráfico é exploratório e não implica correlação estatística.",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6368",
    )
    fig.tight_layout()
    fig.savefig(output, dpi=220, bbox_inches="tight")
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
    plt.rcParams.update(
        {
            "font.size": 10,
            "figure.dpi": 150,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.edgecolor": "#5f6368",
        }
    )
    make_metric_boxplot(
        detail,
        "loc",
        "LOC lógico (lloc)",
        "RQ3 — distribuição de LOC por tratamento",
        figures_dir / "rq3_loc_ia_vs_manual.png",
        decimals=1,
    )
    make_metric_boxplot(
        detail,
        "avg_cyclomatic_complexity",
        "Complexidade ciclomática média por função/método",
        "RQ3 — distribuição da complexidade por tratamento",
        figures_dir / "rq3_complexidade_ia_vs_manual.png",
        decimals=2,
    )
    make_loc_complexity_scatter(
        detail, figures_dir / "rq3_loc_complexidade_scatter.png"
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
        [summarize(detail)]
        + [summarize(detail, participant) for participant in sorted(FINAL_PARTICIPANTS)],
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
