"""Análise estatística e visualização das RQ01 e RQ02 da Sprint 3."""

from __future__ import annotations

import argparse
import math
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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "repositories_s02.csv"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq01_rq02_summary.csv"
)
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "s03"

RQ01_COLUMN = "repository_age_days"
RQ02_COLUMN = "merged_pull_requests"
REQUIRED_COLUMNS = (RQ01_COLUMN, RQ02_COLUMN)

RQ01_UNITS = {
    "total": "records",
    "valid": "records",
    "missing": "records",
    "minimum": "days",
    "maximum": "days",
    "mean": "days",
    "median": "days",
    "standard_deviation": "days",
    "q1": "days",
    "q3": "days",
    "iqr": "days",
    "p10": "days",
    "p90": "days",
    "skewness": "dimensionless",
    "median_years": "years",
}
RQ02_UNITS = {
    "total": "records",
    "valid": "records",
    "missing": "records",
    "minimum": "merged_prs",
    "maximum": "merged_prs",
    "mean": "merged_prs",
    "median": "merged_prs",
    "standard_deviation": "merged_prs",
    "q1": "merged_prs",
    "q3": "merged_prs",
    "iqr": "merged_prs",
    "p10": "merged_prs",
    "p90": "merged_prs",
    "zeros": "records",
    "skewness": "dimensionless",
}

BLUE = "#2563EB"
BLUE_DARK = "#1E3A8A"
BLUE_LIGHT = "#BFDBFE"
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


def _numeric_values(dataframe: pd.DataFrame, column: str) -> pd.Series:
    """Converte uma coluna numérica sem ocultar textos ou valores negativos."""
    if column not in dataframe.columns:
        raise ValueError(f"Coluna obrigatória ausente: {column}")

    source = dataframe[column]
    numeric = pd.to_numeric(source, errors="coerce")
    invalid = source.notna() & numeric.isna()
    if invalid.any():
        invalid_count = int(invalid.sum())
        raise ValueError(
            f"A coluna {column} contém {invalid_count} valor(es) não numérico(s)."
        )

    valid = numeric.dropna().astype(float)
    if valid.empty:
        raise ValueError(f"A coluna {column} não contém valores numéricos válidos.")
    if (valid < 0).any():
        raise ValueError(f"A coluna {column} contém valor(es) negativo(s).")
    return valid


def calculate_distribution_statistics(
    dataframe: pd.DataFrame,
    column: str,
) -> dict[str, float | int]:
    """Calcula as estatísticas descritivas comuns na escala original."""
    valid = _numeric_values(dataframe, column)
    total = int(len(dataframe))
    valid_count = int(valid.count())
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))

    return {
        "total": total,
        "valid": valid_count,
        "missing": total - valid_count,
        "minimum": float(valid.min()),
        "maximum": float(valid.max()),
        "mean": float(valid.mean()),
        "median": float(valid.median()),
        "standard_deviation": float(valid.std(ddof=1)),
        "q1": q1,
        "q3": q3,
        "iqr": q3 - q1,
        "p10": float(valid.quantile(0.10)),
        "p90": float(valid.quantile(0.90)),
        "skewness": float(valid.skew()),
    }


def calculate_rq01_statistics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Calcula a distribuição da idade dos repositórios em dias."""
    statistics = calculate_distribution_statistics(dataframe, RQ01_COLUMN)
    statistics["median_years"] = float(statistics["median"]) / 365.25
    return statistics


def calculate_rq02_statistics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Calcula a distribuição do total de pull requests com status MERGED."""
    statistics = calculate_distribution_statistics(dataframe, RQ02_COLUMN)
    valid = _numeric_values(dataframe, RQ02_COLUMN)
    statistics["zeros"] = int((valid == 0).sum())
    return statistics


def build_summary(
    rq01_statistics: Mapping[str, float | int],
    rq02_statistics: Mapping[str, float | int],
) -> pd.DataFrame:
    """Monta um artefato longo, simples de filtrar por RQ e estatística."""
    rows: list[dict[str, str | float | int]] = []
    for rq, statistics, units in (
        ("RQ01", rq01_statistics, RQ01_UNITS),
        ("RQ02", rq02_statistics, RQ02_UNITS),
    ):
        for statistic, value in statistics.items():
            rows.append(
                {
                    "rq": rq,
                    "statistic": statistic,
                    "value": value,
                    "unit": units[statistic],
                }
            )
    return pd.DataFrame(rows, columns=["rq", "statistic", "value", "unit"])


def save_summary(summary: pd.DataFrame, output_path: Path) -> Path:
    """Persiste as estatísticas sem modificar o dataset bruto."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False, encoding="utf-8")
    return output_path


def should_generate_log_histogram(
    statistics: Mapping[str, float | int],
) -> bool:
    """Decide se a cauda direita compromete a leitura na escala original."""
    p90 = float(statistics["p90"])
    maximum = float(statistics["maximum"])
    skewness = float(statistics["skewness"])
    tail_is_concentrated = maximum > (3 * p90) if p90 > 0 else maximum > 0
    return skewness > 2 and tail_is_concentrated


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


def _histogram(
    values: pd.Series,
    *,
    title: str,
    subtitle: str,
    x_label: str,
    output_path: Path,
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    _prepare_axes(ax)
    ax.hist(values, bins="auto", color=BLUE, edgecolor=BLUE_DARK, linewidth=0.7)
    ax.set_xlabel(x_label, fontsize=11, color=CHARCOAL, labelpad=9)
    ax.set_ylabel("Número de repositórios", fontsize=11, color=CHARCOAL, labelpad=9)
    ax.xaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.yaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.grid(axis="y", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    fig.suptitle(title, fontsize=16, fontweight="bold", color=CHARCOAL, y=0.98)
    ax.set_title(subtitle, fontsize=10.5, color="#4B5563", pad=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save_figure(fig, output_path)


def _boxplot(
    values: pd.Series,
    *,
    title: str,
    subtitle: str,
    x_label: str,
    output_path: Path,
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 4.8))
    _prepare_axes(ax)
    ax.boxplot(
        values,
        orientation="horizontal",
        patch_artist=True,
        widths=0.42,
        boxprops={"facecolor": BLUE_LIGHT, "edgecolor": BLUE_DARK, "linewidth": 1.2},
        medianprops={"color": CHARCOAL, "linewidth": 1.8},
        whiskerprops={"color": BLUE_DARK, "linewidth": 1.1},
        capprops={"color": BLUE_DARK, "linewidth": 1.1},
        flierprops={
            "marker": "o",
            "markerfacecolor": "white",
            "markeredgecolor": BLUE,
            "markersize": 3.5,
            "alpha": 0.65,
        },
    )
    ax.set_yticks([])
    ax.set_xlabel(x_label, fontsize=11, color=CHARCOAL, labelpad=9)
    ax.xaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    fig.suptitle(title, fontsize=16, fontweight="bold", color=CHARCOAL, y=0.98)
    ax.set_title(subtitle, fontsize=10.5, color="#4B5563", pad=12)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return _save_figure(fig, output_path)


def generate_figures(
    dataframe: pd.DataFrame,
    rq02_statistics: Mapping[str, float | int],
    output_dir: Path,
) -> list[Path]:
    """Gera as quatro figuras obrigatórias e, quando útil, a visão log1p."""
    age = _numeric_values(dataframe, RQ01_COLUMN)
    merged_prs = _numeric_values(dataframe, RQ02_COLUMN)
    sample_age = f"Escala original em dias; n = {len(age):,}".replace(",", ".")
    sample_prs = (
        f"Escala original; total acumulado por repositório; n = {len(merged_prs):,}"
        .replace(",", ".")
    )

    generated = [
        _histogram(
            age,
            title="Distribuição da idade dos repositórios populares",
            subtitle=sample_age,
            x_label="Idade do repositório (dias)",
            output_path=output_dir / "rq01_age_histogram.png",
        ),
        _boxplot(
            age,
            title="Dispersão da idade dos repositórios populares",
            subtitle=sample_age,
            x_label="Idade do repositório (dias)",
            output_path=output_dir / "rq01_age_boxplot.png",
        ),
        _histogram(
            merged_prs,
            title="Distribuição de pull requests merged por repositório",
            subtitle=sample_prs,
            x_label="Pull requests merged (quantidade)",
            output_path=output_dir / "rq02_merged_prs_histogram.png",
        ),
        _boxplot(
            merged_prs,
            title="Dispersão de pull requests merged por repositório",
            subtitle=sample_prs,
            x_label="Pull requests merged (quantidade)",
            output_path=output_dir / "rq02_merged_prs_boxplot.png",
        ),
    ]

    if should_generate_log_histogram(rq02_statistics):
        log_values = merged_prs.map(math.log1p)
        generated.append(
            _histogram(
                log_values,
                title="Distribuição de pull requests merged em escala log1p",
                subtitle=(
                    "Transformação somente visual: log1p(x); "
                    f"estatísticas mantidas na escala original; n = {len(log_values):,}"
                ).replace(",", "."),
                x_label="log1p(pull requests merged)",
                output_path=output_dir / "rq02_merged_prs_log_histogram.png",
            )
        )

    return generated


def interpret_rq01(statistics: Mapping[str, float | int]) -> str:
    """Produz uma interpretação cautelosa da distribuição completa da RQ01."""
    return (
        f"A idade típica é de {statistics['median']:.1f} dias "
        f"(aproximadamente {statistics['median_years']:.1f} anos). "
        f"A metade central está entre {statistics['q1']:.1f} e "
        f"{statistics['q3']:.1f} dias (IQR de {statistics['iqr']:.1f} dias), "
        "o que indica dispersão relevante. "
        f"A amplitude de {statistics['minimum']:.0f} a {statistics['maximum']:.0f} "
        "dias mostra a coexistência de projetos recentes e muito antigos; os dados "
        "sugerem predominância de repositórios maduros, sem indicar que todos o sejam."
    )


def interpret_rq02(statistics: Mapping[str, float | int]) -> str:
    """Produz uma interpretação cautelosa da distribuição completa da RQ02."""
    return (
        f"O valor típico é de {statistics['median']:.1f} pull requests merged, "
        f"enquanto a média é {statistics['mean']:.1f}. "
        f"A assimetria de {statistics['skewness']:.2f} e a amplitude até "
        f"{statistics['maximum']:.0f} indicam uma cauda direita pronunciada, na qual "
        "poucos projetos concentram valores muito elevados. "
        f"Há {statistics['zeros']} repositório(s) sem PR merged; a análise descreve "
        "a distribuição completa e não implica origem externa das contribuições."
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
    rq01_statistics: Mapping[str, float | int],
    rq02_statistics: Mapping[str, float | int],
    artifacts: list[Path],
) -> None:
    """Exibe somente o resumo necessário para acompanhar a execução."""
    print("SPRINT 3 — RQ01/RQ02")
    print("\nDataset")
    print(f"- registros: {_format_number(record_count)}")

    for rq, statistics, fields in (
        (
            "RQ01",
            rq01_statistics,
            ("valid", "mean", "median", "q1", "q3", "minimum", "maximum", "skewness"),
        ),
        (
            "RQ02",
            rq02_statistics,
            ("valid", "mean", "median", "q1", "q3", "minimum", "maximum", "zeros", "skewness"),
        ),
    ):
        print(f"\n{rq}")
        for field in fields:
            print(f"- {field}: {_format_number(statistics[field])}")

    print("\nInterpretação RQ01")
    print(interpret_rq01(rq01_statistics))
    print("\nInterpretação RQ02")
    print(interpret_rq02(rq02_statistics))
    print("\nArtefatos gerados:")
    for artifact in artifacts:
        print(f"- {_display_path(artifact)}")


def run_analysis(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
) -> tuple[dict[str, float | int], dict[str, float | int], list[Path]]:
    """Executa a análise completa e reproduzível das RQ01/RQ02."""
    dataframe = load_dataset(input_path)
    rq01_statistics = calculate_rq01_statistics(dataframe)
    rq02_statistics = calculate_rq02_statistics(dataframe)
    summary = build_summary(rq01_statistics, rq02_statistics)
    summary_file = save_summary(summary, summary_path)
    figure_files = generate_figures(dataframe, rq02_statistics, figures_dir)
    artifacts = [summary_file, *figure_files]
    print_execution_summary(
        len(dataframe), rq01_statistics, rq02_statistics, artifacts
    )
    return rq01_statistics, rq02_statistics, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa RQ01 e RQ02 a partir do dataset validado da Sprint 2."
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
