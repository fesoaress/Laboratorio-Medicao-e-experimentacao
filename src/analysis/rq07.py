"""Análise estatística e visualização da RQ07 (bônus) da Sprint 3.

Agrupa os repositórios pela linguagem principal (RQ05) e relaciona as
medianas de RQ02 (pull requests merged), RQ03 (releases) e RQ04 (dias desde
o último push) à posição da linguagem no TIOBE Index de agosto/2026 — sem
inferir causalidade, apenas associação.
"""
from __future__ import annotations

import argparse
import os
import tempfile
from pathlib import Path
from typing import Mapping

os.environ.setdefault(
    "MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lab01_matplotlib")
)

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from matplotlib.ticker import FuncFormatter

from src.analysis.rq05_rq06 import LANGUAGE_NOT_INFORMED, TIOBE_TOP_10

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "repositories_s02.csv"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq07_summary.csv"
)
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "s03"

LANGUAGE_COLUMN = "primary_language"
RQ02_COLUMN = "merged_pull_requests"
RQ03_COLUMN = "release_count"
RQ04_COLUMN = "days_since_last_update"
REQUIRED_COLUMNS = (LANGUAGE_COLUMN, RQ02_COLUMN, RQ03_COLUMN, RQ04_COLUMN)

# Tamanho mínimo de amostra por linguagem para entrar nos rankings — evita que
# uma linguagem com 1-2 repositórios distorça a mediana visualmente.
MIN_LANGUAGE_SAMPLE_SIZE = 15
TOP_LANGUAGES_LIMIT = 12

METRIC_LABELS = {
    RQ02_COLUMN: "PRs merged (mediana)",
    RQ03_COLUMN: "Releases (mediana)",
    RQ04_COLUMN: "Dias desde o último push (mediana)",
}

BLUE = "#2563EB"
BLUE_DARK = "#1E3A8A"
GOLD = "#D97706"
GOLD_DARK = "#92400E"
CHARCOAL = "#1F2937"
GRID = "#D1D5DB"


def load_dataset(input_path: Path = DEFAULT_INPUT_PATH) -> pd.DataFrame:
    """Carrega o CSV da Sprint 2 e valida as colunas exigidas."""
    dataframe = pd.read_csv(input_path)
    validate_required_columns(dataframe)
    return dataframe


def validate_required_columns(dataframe: pd.DataFrame) -> None:
    """Falha com mensagem clara quando uma métrica necessária está ausente."""
    missing_columns = [
        column for column in REQUIRED_COLUMNS if column not in dataframe.columns
    ]
    if missing_columns:
        raise ValueError(
            "Colunas obrigatórias ausentes: " + ", ".join(missing_columns)
        )


def build_language_summary(dataframe: pd.DataFrame) -> pd.DataFrame:
    """Agrupa por linguagem e calcula n e medianas de RQ02/RQ03/RQ04."""
    data = dataframe.copy()
    data[LANGUAGE_COLUMN] = data[LANGUAGE_COLUMN].fillna(LANGUAGE_NOT_INFORMED)
    for column in (RQ02_COLUMN, RQ03_COLUMN, RQ04_COLUMN):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    grouped = (
        data.groupby(LANGUAGE_COLUMN)
        .agg(
            n=(LANGUAGE_COLUMN, "size"),
            median_merged_pull_requests=(RQ02_COLUMN, "median"),
            median_release_count=(RQ03_COLUMN, "median"),
            median_days_since_last_update=(RQ04_COLUMN, "median"),
        )
        .reset_index()
        .rename(columns={LANGUAGE_COLUMN: "language"})
    )
    grouped["in_tiobe_top10"] = grouped["language"].isin(TIOBE_TOP_10)
    grouped = grouped[grouped["language"] != LANGUAGE_NOT_INFORMED]
    return grouped.sort_values("n", ascending=False).reset_index(drop=True)


def build_tiobe_comparison(
    dataframe: pd.DataFrame,
) -> dict[str, dict[str, float | int]]:
    """Compara medianas entre repositórios em linguagens do TIOBE top 10 e os demais."""
    data = dataframe.copy()
    data[LANGUAGE_COLUMN] = data[LANGUAGE_COLUMN].fillna(LANGUAGE_NOT_INFORMED)
    for column in (RQ02_COLUMN, RQ03_COLUMN, RQ04_COLUMN):
        data[column] = pd.to_numeric(data[column], errors="coerce")

    is_top10 = data[LANGUAGE_COLUMN].isin(TIOBE_TOP_10)
    top10_group = data.loc[is_top10]
    other_group = data.loc[~is_top10 & (data[LANGUAGE_COLUMN] != LANGUAGE_NOT_INFORMED)]

    result: dict[str, dict[str, float | int]] = {}
    for column in (RQ02_COLUMN, RQ03_COLUMN, RQ04_COLUMN):
        result[column] = {
            "tiobe_top10_n": int(top10_group[column].count()),
            "tiobe_top10_median": float(top10_group[column].median()),
            "other_n": int(other_group[column].count()),
            "other_median": float(other_group[column].median()),
        }
    return result


def save_csv(dataframe: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def _format_thousands(value: float, _position: int) -> str:
    return f"{value:,.0f}".replace(",", ".")


def _prepare_axes(ax: plt.Axes) -> None:
    ax.set_facecolor("white")
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color(CHARCOAL)
    ax.spines["bottom"].set_color(CHARCOAL)
    ax.tick_params(colors=CHARCOAL, labelsize=10)


def _save_figure(fig: plt.Figure, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def generate_language_ranking_figure(
    language_summary: pd.DataFrame,
    metric_column: str,
    output_path: Path,
) -> Path:
    """Gera um ranking horizontal da mediana de uma métrica por linguagem."""
    eligible = language_summary[
        language_summary["n"] >= MIN_LANGUAGE_SAMPLE_SIZE
    ].copy()
    metric_map = {
        RQ02_COLUMN: "median_merged_pull_requests",
        RQ03_COLUMN: "median_release_count",
        RQ04_COLUMN: "median_days_since_last_update",
    }
    value_column = metric_map[metric_column]
    eligible = eligible.sort_values(value_column, ascending=False).head(
        TOP_LANGUAGES_LIMIT
    )
    eligible = eligible.iloc[::-1]

    colors = [
        BLUE if is_top10 else GOLD for is_top10 in eligible["in_tiobe_top10"]
    ]
    edge_colors = [
        BLUE_DARK if is_top10 else GOLD_DARK for is_top10 in eligible["in_tiobe_top10"]
    ]

    fig, ax = plt.subplots(figsize=(10, 6.5))
    _prepare_axes(ax)
    bars = ax.barh(
        eligible["language"],
        eligible[value_column],
        color=colors,
        edgecolor=edge_colors,
        linewidth=0.8,
    )
    max_value = eligible[value_column].max()
    for bar, value, n in zip(bars, eligible[value_column], eligible["n"]):
        ax.text(
            bar.get_width() + max_value * 0.015,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,.0f} (n={n})".replace(",", "."),
            va="center",
            fontsize=8.5,
            color=CHARCOAL,
        )
    ax.set_xlabel(
        METRIC_LABELS[metric_column], fontsize=11, color=CHARCOAL, labelpad=9
    )
    ax.xaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)

    from matplotlib.patches import Patch

    legend_handles = [
        Patch(facecolor=BLUE, edgecolor=BLUE_DARK, label="TIOBE top 10"),
        Patch(facecolor=GOLD, edgecolor=GOLD_DARK, label="Fora do TIOBE top 10"),
    ]
    ax.legend(handles=legend_handles, frameon=False, loc="lower right", fontsize=9)

    fig.suptitle(
        f"RQ07 — {METRIC_LABELS[metric_column]} por linguagem",
        fontsize=15,
        fontweight="bold",
        color=CHARCOAL,
        y=0.98,
    )
    ax.set_title(
        f"Linguagens com pelo menos {MIN_LANGUAGE_SAMPLE_SIZE} repositórios na amostra",
        fontsize=10,
        color="#4B5563",
        pad=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.92))
    return _save_figure(fig, output_path)


def generate_tiobe_comparison_figure(
    comparison: Mapping[str, Mapping[str, float | int]],
    output_path: Path,
) -> Path:
    """Gera 3 subgráficos comparando medianas: TIOBE top 10 vs demais linguagens."""
    metrics = [RQ02_COLUMN, RQ03_COLUMN, RQ04_COLUMN]
    fig, axes = plt.subplots(1, 3, figsize=(15, 5.5))

    for ax, metric in zip(axes, metrics):
        _prepare_axes(ax)
        values = [
            comparison[metric]["tiobe_top10_median"],
            comparison[metric]["other_median"],
        ]
        labels = ["TIOBE top 10", "Outras"]
        bars = ax.bar(
            labels,
            values,
            color=[BLUE, GOLD],
            edgecolor=[BLUE_DARK, GOLD_DARK],
            linewidth=0.9,
            width=0.55,
        )
        max_value = max(values) if max(values) > 0 else 1
        for bar, value in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                value + max_value * 0.02,
                f"{value:,.1f}".replace(",", "."),
                ha="center",
                fontsize=10,
                color=CHARCOAL,
            )
        ax.set_ylim(0, max_value * 1.2)
        ax.set_title(METRIC_LABELS[metric], fontsize=11, color=CHARCOAL, pad=10)
        ax.yaxis.set_major_formatter(FuncFormatter(_format_thousands))
        ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
        ax.set_axisbelow(True)

    fig.suptitle(
        "RQ07 — Medianas por grupo de linguagem (TIOBE top 10 vs. demais)",
        fontsize=15,
        fontweight="bold",
        color=CHARCOAL,
        y=1.02,
    )
    fig.text(
        0.5,
        0.94,
        "Associação, não causalidade — comparação descritiva entre grupos",
        ha="center",
        fontsize=10,
        color="#4B5563",
    )
    fig.tight_layout(rect=(0, 0, 1, 0.90))
    return _save_figure(fig, output_path)


def generate_figures(
    language_summary: pd.DataFrame,
    comparison: Mapping[str, Mapping[str, float | int]],
    output_dir: Path,
) -> list[Path]:
    """Gera as quatro figuras da RQ07."""
    figures = [
        generate_language_ranking_figure(
            language_summary, RQ02_COLUMN, output_dir / "rq07_ranking_rq02.png"
        ),
        generate_language_ranking_figure(
            language_summary, RQ03_COLUMN, output_dir / "rq07_ranking_rq03.png"
        ),
        generate_language_ranking_figure(
            language_summary, RQ04_COLUMN, output_dir / "rq07_ranking_rq04.png"
        ),
        generate_tiobe_comparison_figure(
            comparison, output_dir / "rq07_tiobe_comparison.png"
        ),
    ]
    return figures


def interpret_rq07(
    comparison: Mapping[str, Mapping[str, float | int]],
) -> str:
    """Produz uma interpretação cautelosa da comparação TIOBE top 10 vs demais."""
    rq02 = comparison[RQ02_COLUMN]
    rq03 = comparison[RQ03_COLUMN]
    rq04 = comparison[RQ04_COLUMN]

    prs_direction = (
        "maior" if rq02["tiobe_top10_median"] > rq02["other_median"] else "menor"
    )
    releases_direction = (
        "maior" if rq03["tiobe_top10_median"] > rq03["other_median"] else "menor"
    )
    # RQ04 é "dias desde o último push": menor valor = atualização mais recente.
    update_direction = (
        "mais recente"
        if rq04["tiobe_top10_median"] < rq04["other_median"]
        else "menos recente"
    )

    return (
        f"Repositórios em linguagens do TIOBE top 10 apresentam mediana "
        f"{prs_direction} de pull requests merged "
        f"({rq02['tiobe_top10_median']:.0f} vs. {rq02['other_median']:.0f} "
        "nas demais linguagens), mediana "
        f"{releases_direction} de releases "
        f"({rq03['tiobe_top10_median']:.0f} vs. {rq03['other_median']:.0f}), "
        f"e atualização {update_direction} "
        f"({rq04['tiobe_top10_median']:.0f} vs. {rq04['other_median']:.0f} "
        "dias desde o último push). Trata-se de uma associação descritiva "
        "entre grupos de linguagem, sem controle de outras variáveis "
        "(ex.: idade do repositório, domínio do projeto) e sem implicação "
        "de causalidade entre popularidade da linguagem e essas métricas."
    )


def _format_number(value: float | int) -> str:
    if isinstance(value, int):
        return f"{value:,}".replace(",", ".")
    return f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT))
    except ValueError:
        return str(path)


def print_execution_summary(
    record_count: int,
    language_summary: pd.DataFrame,
    comparison: Mapping[str, Mapping[str, float | int]],
    artifacts: list[Path],
) -> None:
    """Exibe somente o resumo necessário para acompanhar a execução."""
    print("SPRINT 3 — RQ07 (bônus)")
    print("\nDataset")
    print(f"- registros: {_format_number(record_count)}")
    print(
        f"- linguagens elegíveis (n >= {MIN_LANGUAGE_SAMPLE_SIZE}): "
        f"{(language_summary['n'] >= MIN_LANGUAGE_SAMPLE_SIZE).sum()}"
    )

    print("\nComparação TIOBE top 10 vs. demais")
    for metric, label in METRIC_LABELS.items():
        data = comparison[metric]
        print(f"- {label}")
        print(
            f"  TIOBE top 10 (n={data['tiobe_top10_n']}): "
            f"mediana {_format_number(data['tiobe_top10_median'])}"
        )
        print(
            f"  Outras (n={data['other_n']}): "
            f"mediana {_format_number(data['other_median'])}"
        )

    print("\nInterpretação RQ07")
    print(interpret_rq07(comparison))

    print("\nArtefatos gerados:")
    for artifact in artifacts:
        print(f"- {_display_path(artifact)}")


def run_analysis(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
) -> tuple[pd.DataFrame, dict[str, dict[str, float | int]], list[Path]]:
    """Executa a análise completa e reproduzível da RQ07."""
    dataframe = load_dataset(input_path)
    language_summary = build_language_summary(dataframe)
    comparison = build_tiobe_comparison(dataframe)
    summary_file = save_csv(language_summary, summary_path)
    figure_files = generate_figures(language_summary, comparison, figures_dir)
    artifacts = [summary_file, *figure_files]
    print_execution_summary(len(dataframe), language_summary, comparison, artifacts)
    return language_summary, comparison, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa RQ07 (bônus) a partir do dataset validado da Sprint 2."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_SUMMARY_PATH)
    parser.add_argument("--figures-dir", type=Path, default=DEFAULT_FIGURES_DIR)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_analysis(
        input_path=args.input,
        summary_path=args.summary,
        figures_dir=args.figures_dir,
    )

if __name__ == "__main__":
    main()