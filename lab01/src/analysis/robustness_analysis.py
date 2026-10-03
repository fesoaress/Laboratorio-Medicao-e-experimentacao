"""Análise complementar de robustez a valores extremos segundo o critério IQR.

A análise oficial das RQ01/RQ02 permanece baseada nos 1.000 repositórios. Este
módulo cria apenas uma visão de sensibilidade, sem modificar a série recebida ou
qualquer artefato da análise principal.
"""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Mapping

import pandas as pd

from src.analysis.rq01_rq02 import (
    DEFAULT_INPUT_PATH,
    PROJECT_ROOT,
    RQ01_COLUMN,
    RQ02_COLUMN,
    load_dataset,
)

import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


DEFAULT_ROBUSTNESS_SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq01_rq02_robustness.csv"
)
DEFAULT_OUTLIERS_PATH = (
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq01_rq02_outliers.csv"
)
DEFAULT_FIGURE_PATH = (
    PROJECT_ROOT
    / "reports"
    / "figures"
    / "s03"
    / "rq01_rq02_robustness_percent_change.png"
)

REPOSITORY_COLUMN = "name_with_owner"
IQR_MULTIPLIER = 1.5

BLUE = "#2563EB"
BLUE_DARK = "#1E3A8A"
GOLD = "#D97706"
GOLD_DARK = "#92400E"
CHARCOAL = "#1F2937"
GRID = "#D1D5DB"


@dataclass(frozen=True)
class RobustnessResult:
    """Resultado imutável da análise de uma série numérica."""

    total: int
    valid: int
    missing: int
    q1: float
    q3: float
    iqr: float
    lower_bound: float
    upper_bound: float
    outlier_count: int
    outlier_percentage: float
    original_count: int
    original_mean: float
    original_median: float
    original_standard_deviation: float | None
    original_minimum: float
    original_maximum: float
    filtered_count: int
    filtered_mean: float
    filtered_median: float
    filtered_standard_deviation: float | None
    filtered_minimum: float
    filtered_maximum: float
    mean_absolute_change: float
    mean_percent_change: float | None
    median_absolute_change: float
    median_percent_change: float | None

    def as_metrics(self) -> dict[str, float | int | None]:
        return asdict(self)


def _numeric_series(series: pd.Series) -> pd.Series:
    """Valida e copia os valores numéricos, preservando o índice original."""
    numeric = pd.to_numeric(series, errors="coerce")
    invalid = series.notna() & numeric.isna()
    if invalid.any():
        raise ValueError(
            f"A série contém {int(invalid.sum())} valor(es) não numérico(s)."
        )
    valid = numeric.dropna().astype(float)
    if valid.empty:
        raise ValueError("A série deve conter ao menos um valor numérico válido.")
    return valid.copy()


def _standard_deviation(series: pd.Series) -> float | None:
    if len(series) < 2:
        return None
    return float(series.std(ddof=1))


def calculate_percent_change(
    original_value: float,
    filtered_value: float,
) -> float | None:
    """Calcula variação assinada; retorna None quando o original é zero."""
    if original_value == 0:
        return None
    return ((filtered_value - original_value) / original_value) * 100


def analyze_robustness(series: pd.Series) -> RobustnessResult:
    """Compara medidas completas e sem extremos definidos por 1,5 × IQR.

    O percentual de extremos usa como denominador o número de valores válidos.
    A diferença absoluta é ``abs(valor_filtrado - valor_original)``; a variação
    percentual é assinada e segue ``((filtrado - original) / original) * 100``.
    """
    valid = _numeric_series(series)
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    iqr = q3 - q1
    lower_bound = q1 - IQR_MULTIPLIER * iqr
    upper_bound = q3 + IQR_MULTIPLIER * iqr
    outlier_mask = (valid < lower_bound) | (valid > upper_bound)
    filtered = valid.loc[~outlier_mask].copy()

    if filtered.empty:
        raise ValueError("O critério IQR não deixou valores para a visão filtrada.")

    original_mean = float(valid.mean())
    filtered_mean = float(filtered.mean())
    original_median = float(valid.median())
    filtered_median = float(filtered.median())
    outlier_count = int(outlier_mask.sum())

    return RobustnessResult(
        total=int(len(series)),
        valid=int(len(valid)),
        missing=int(len(series) - len(valid)),
        q1=q1,
        q3=q3,
        iqr=iqr,
        lower_bound=lower_bound,
        upper_bound=upper_bound,
        outlier_count=outlier_count,
        outlier_percentage=(outlier_count / len(valid)) * 100,
        original_count=int(len(valid)),
        original_mean=original_mean,
        original_median=original_median,
        original_standard_deviation=_standard_deviation(valid),
        original_minimum=float(valid.min()),
        original_maximum=float(valid.max()),
        filtered_count=int(len(filtered)),
        filtered_mean=filtered_mean,
        filtered_median=filtered_median,
        filtered_standard_deviation=_standard_deviation(filtered),
        filtered_minimum=float(filtered.min()),
        filtered_maximum=float(filtered.max()),
        mean_absolute_change=abs(filtered_mean - original_mean),
        mean_percent_change=calculate_percent_change(original_mean, filtered_mean),
        median_absolute_change=abs(filtered_median - original_median),
        median_percent_change=calculate_percent_change(
            original_median, filtered_median
        ),
    )


def _metric_unit(metric: str, value_unit: str) -> str:
    if metric in {
        "total",
        "valid",
        "missing",
        "outlier_count",
        "original_count",
        "filtered_count",
    }:
        return "records"
    if metric in {
        "outlier_percentage",
        "mean_percent_change",
        "median_percent_change",
    }:
        return "percent"
    return value_unit


def build_robustness_summary(
    results: Mapping[str, RobustnessResult],
) -> pd.DataFrame:
    """Cria summary longo e explícito para RQ01 e RQ02."""
    value_units = {"RQ01": "days", "RQ02": "merged_prs"}
    rows: list[dict[str, str | float | int | None]] = []
    for rq, result in results.items():
        for metric, value in result.as_metrics().items():
            rows.append(
                {
                    "rq": rq,
                    "metric": metric,
                    "value": value,
                    "unit": _metric_unit(metric, value_units[rq]),
                }
            )
    return pd.DataFrame(rows, columns=["rq", "metric", "value", "unit"])


def build_outlier_records(
    dataframe: pd.DataFrame,
    *,
    rq: str,
    value_column: str,
    result: RobustnessResult,
    repository_column: str = REPOSITORY_COLUMN,
) -> pd.DataFrame:
    """Identifica os registros fora dos limites sem alterar o dataframe."""
    if repository_column not in dataframe.columns:
        raise ValueError(f"Coluna de identificação ausente: {repository_column}")
    if value_column not in dataframe.columns:
        raise ValueError(f"Coluna de métrica ausente: {value_column}")

    valid = _numeric_series(dataframe[value_column])
    mask = (valid < result.lower_bound) | (valid > result.upper_bound)
    outlier_values = valid.loc[mask]
    if outlier_values.empty:
        return pd.DataFrame(
            columns=[
                "rq",
                "repository",
                "metric_column",
                "value",
                "lower_bound",
                "upper_bound",
                "reason",
            ]
        )

    repositories = dataframe.loc[outlier_values.index, repository_column]
    reasons = outlier_values.map(
        lambda value: (
            "below_lower_bound"
            if value < result.lower_bound
            else "above_upper_bound"
        )
    )
    return pd.DataFrame(
        {
            "rq": rq,
            "repository": repositories.astype(str),
            "metric_column": value_column,
            "value": outlier_values,
            "lower_bound": result.lower_bound,
            "upper_bound": result.upper_bound,
            "reason": reasons,
        }
    ).reset_index(drop=True)


def save_csv(dataframe: pd.DataFrame, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    dataframe.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def _format_percent_axis(value: float, _position: int) -> str:
    return f"{value:.0f}%".replace("-0%", "0%")


def generate_robustness_figure(
    results: Mapping[str, RobustnessResult],
    output_path: Path,
) -> Path:
    """Compara variações percentuais sem misturar as unidades das RQs."""
    rq_labels = ["RQ01", "RQ02"]
    mean_changes = [results[rq].mean_percent_change for rq in rq_labels]
    median_changes = [results[rq].median_percent_change for rq in rq_labels]
    if any(value is None for value in [*mean_changes, *median_changes]):
        raise ValueError(
            "A figura exige variações percentuais matematicamente definidas."
        )

    mean_values = [float(value) for value in mean_changes if value is not None]
    median_values = [float(value) for value in median_changes if value is not None]
    positions = list(range(len(rq_labels)))
    width = 0.34

    fig, ax = plt.subplots(figsize=(10, 6))
    mean_bars = ax.bar(
        [position - width / 2 for position in positions],
        mean_values,
        width,
        label="Média",
        color=BLUE,
        edgecolor=BLUE_DARK,
        linewidth=0.9,
    )
    median_bars = ax.bar(
        [position + width / 2 for position in positions],
        median_values,
        width,
        label="Mediana",
        color=GOLD,
        edgecolor=GOLD_DARK,
        linewidth=0.9,
    )

    all_values = [*mean_values, *median_values, 0.0]
    span = max(all_values) - min(all_values)
    label_offset = max(span * 0.025, 0.7)
    for bar in [*mean_bars, *median_bars]:
        value = float(bar.get_height())
        vertical_alignment = "top" if value < 0 else "bottom"
        y = value - label_offset if value < 0 else value + label_offset
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            y,
            f"{value:+.2f}%" if value else "0,00%",
            ha="center",
            va=vertical_alignment,
            fontsize=10,
            color=CHARCOAL,
        )

    padding = max(span * 0.16, 5.0)
    ax.set_ylim(min(all_values) - padding, max(all_values) + padding)
    ax.axhline(0, color=CHARCOAL, linewidth=1.1)
    ax.set_xticks(positions, rq_labels)
    ax.set_ylabel(
        "Variação após exclusão dos extremos IQR (%)",
        fontsize=11,
        color=CHARCOAL,
        labelpad=9,
    )
    ax.yaxis.set_major_formatter(FuncFormatter(_format_percent_axis))
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color(CHARCOAL)
    ax.spines["bottom"].set_color(CHARCOAL)
    ax.tick_params(colors=CHARCOAL, labelsize=10)
    ax.legend(frameon=False, loc="upper right", ncols=2)
    fig.suptitle(
        "Sensibilidade das medidas-resumo a valores extremos IQR",
        fontsize=16,
        fontweight="bold",
        color=CHARCOAL,
        y=0.98,
    )
    ax.set_title(
        "Variação percentual assinada; análise complementar, sem alterar a amostra oficial",
        fontsize=10.5,
        color="#4B5563",
        pad=12,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=300, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return output_path


def _format_number(value: float | int | None) -> str:
    if value is None:
        return "N/A"
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
    results: Mapping[str, RobustnessResult],
    artifacts: list[Path],
) -> None:
    print("SPRINT 3 — ANÁLISE DE ROBUSTEZ")
    print("\nDataset")
    print(f"- registros: {_format_number(record_count)}")
    for rq, result in results.items():
        print(f"\n{rq}")
        print(f"- IQR: {_format_number(result.iqr)}")
        print(
            "- limites: "
            f"[{_format_number(result.lower_bound)}, "
            f"{_format_number(result.upper_bound)}]"
        )
        print(f"- extremos: {_format_number(result.outlier_count)}")
        print(f"- percentual: {_format_number(result.outlier_percentage)}%")
        print(f"- média original: {_format_number(result.original_mean)}")
        print(f"- média sem extremos: {_format_number(result.filtered_mean)}")
        print(
            "- variação da média: "
            f"{_format_number(result.mean_percent_change)}%"
        )
        print(f"- mediana original: {_format_number(result.original_median)}")
        print(f"- mediana sem extremos: {_format_number(result.filtered_median)}")
        print(
            "- variação da mediana: "
            f"{_format_number(result.median_percent_change)}%"
        )

    print("\nArtefatos:")
    for artifact in artifacts:
        print(f"- {_display_path(artifact)}")


def run_robustness_analysis(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    summary_path: Path = DEFAULT_ROBUSTNESS_SUMMARY_PATH,
    outliers_path: Path = DEFAULT_OUTLIERS_PATH,
    figure_path: Path = DEFAULT_FIGURE_PATH,
) -> tuple[dict[str, RobustnessResult], list[Path]]:
    """Executa a contribuição de robustez somente para RQ01 e RQ02."""
    dataframe = load_dataset(input_path)
    if REPOSITORY_COLUMN not in dataframe.columns:
        raise ValueError(f"Coluna obrigatória ausente: {REPOSITORY_COLUMN}")

    specifications = {
        "RQ01": RQ01_COLUMN,
        "RQ02": RQ02_COLUMN,
    }
    results = {
        rq: analyze_robustness(dataframe[column])
        for rq, column in specifications.items()
    }
    summary = build_robustness_summary(results)
    summary_file = save_csv(summary, summary_path)

    outlier_frames = [
        build_outlier_records(
            dataframe,
            rq=rq,
            value_column=column,
            result=results[rq],
        )
        for rq, column in specifications.items()
    ]
    outliers = pd.concat(outlier_frames, ignore_index=True)
    outliers_file = save_csv(outliers, outliers_path)
    figure_file = generate_robustness_figure(results, figure_path)
    artifacts = [summary_file, outliers_file, figure_file]
    print_execution_summary(len(dataframe), results, artifacts)
    return results, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Executa análise complementar de robustez IQR para RQ01/RQ02."
    )
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT_PATH)
    parser.add_argument("--summary", type=Path, default=DEFAULT_ROBUSTNESS_SUMMARY_PATH)
    parser.add_argument("--outliers", type=Path, default=DEFAULT_OUTLIERS_PATH)
    parser.add_argument("--figure", type=Path, default=DEFAULT_FIGURE_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    run_robustness_analysis(
        input_path=args.input,
        summary_path=args.summary,
        outliers_path=args.outliers,
        figure_path=args.figure,
    )


if __name__ == "__main__":
    main()
