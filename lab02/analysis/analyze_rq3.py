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
import pandas as pd

from lab02.analysis.analyze_rq1_rq2 import (
    COLORS,
    FIGURES_DIR,
    RESULTS_DIR,
    load_and_audit,
    require,
)
from lab02.metrics.run_metrics import DEFAULT_RESULTS_DIR


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
    _, trials, _ = load_and_audit()
    fernanda = trials.loc[trials.participante == "Fernanda"]
    if require_fernanda:
        require(
            len(fernanda) == 4
            and fernanda.kata.nunique() == 4
            and fernanda.tratamento.value_counts().to_dict()
            == {"IA": 2, "Manual": 2},
            "os quatro trials oficiais de Fernanda ainda não estão completos",
        )

    metrics = pd.read_csv(
        METRICS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig"
    )
    require(METRIC_COLUMNS <= set(metrics), "metrics.csv: colunas obrigatórias ausentes")
    metrics = metrics.loc[metrics.source_kind == "observed"].copy()
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


def make_figures(detail: pd.DataFrame, figures_dir: Path) -> None:
    figures_dir.mkdir(parents=True, exist_ok=True)
    plt.rcParams.update({"font.size": 9, "figure.dpi": 140})
    for column, ylabel, filename in METRICS:
        fig, ax = plt.subplots(figsize=(9, 5))
        for x, treatment in enumerate(("IA", "Manual")):
            group = detail.loc[detail.tratamento == treatment].sort_values(
                ["participante", "kata"]
            )
            offsets = [
                (index - (len(group) - 1) / 2) * 0.18 for index in range(len(group))
            ]
            for point_index, (offset, (_, row)) in enumerate(zip(offsets, group.iterrows())):
                if pd.isna(row[column]):
                    continue
                ax.scatter(x + offset, row[column], color=COLORS[treatment], s=58)
                label_y = 8 if point_index % 2 == 0 else -10
                ax.annotate(
                    f"{row.participante} · K{row.kata[4]}",
                    (x + offset, row[column]),
                    xytext=(0, label_y),
                    textcoords="offset points",
                    fontsize=7,
                    ha="center",
                    va="bottom" if label_y > 0 else "top",
                )
            values = group[column].dropna()
            if not values.empty:
                ax.hlines(
                    values.median(),
                    x - 0.25,
                    x + 0.25,
                    colors=COLORS[treatment],
                    linewidth=2,
                    label=f"Mediana {treatment}: {values.median():.2f}",
                )
        ax.set(
            xlim=(-0.55, 1.55),
            xticks=[0, 1],
            xticklabels=["IA", "Manual"],
            ylabel=ylabel,
            title=f"RQ3 — {ylabel} por trial",
        )
        ax.grid(axis="y", alpha=0.25)
        ax.legend(loc="best")
        fig.tight_layout()
        fig.savefig(figures_dir / filename)
        plt.close(fig)


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
