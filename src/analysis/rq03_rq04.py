"""Análise estatística e visualização das RQ03 e RQ04 da Sprint 3."""

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


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_INPUT_PATH = PROJECT_ROOT / "data" / "raw" / "repositories_s02.csv"
DEFAULT_SUMMARY_PATH = (
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq03_rq04_summary.csv"
)
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "s03"

RQ03_COLUMN = "release_count"
RQ04_COLUMN = "days_since_last_update"
REQUIRED_COLUMNS = (RQ03_COLUMN, RQ04_COLUMN)

# Teto da API GraphQL para releases { totalCount }
API_RELEASE_CEILING = 1000

RQ03_UNITS = {
    "total": "records",
    "valid": "records",
    "missing": "records",
    "minimum": "releases",
    "maximum": "releases",
    "mean": "releases",
    "median": "releases",
    "standard_deviation": "releases",
    "q1": "releases",
    "q3": "releases",
    "iqr": "releases",
    "p10": "releases",
    "p90": "releases",
    "zeros": "records",
    "at_ceiling": "records",
    "skewness": "dimensionless",
}
RQ04_UNITS = {
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
    "zeros": "records",
    "above_365": "records",
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


def calculate_rq03_statistics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Calcula a distribuição do total de GitHub Releases formais."""
    statistics = calculate_distribution_statistics(dataframe, RQ03_COLUMN)
    valid = _numeric_values(dataframe, RQ03_COLUMN)
    statistics["zeros"] = int((valid == 0).sum())
    statistics["at_ceiling"] = int((valid == API_RELEASE_CEILING).sum())
    return statistics


def calculate_rq04_statistics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Calcula a distribuição do tempo em dias desde o último push."""
    statistics = calculate_distribution_statistics(dataframe, RQ04_COLUMN)
    valid = _numeric_values(dataframe, RQ04_COLUMN)
    statistics["zeros"] = int((valid == 0).sum())
    statistics["above_365"] = int((valid > 365).sum())
    return statistics


def build_summary(
    rq03_statistics: Mapping[str, float | int],
    rq04_statistics: Mapping[str, float | int],
) -> pd.DataFrame:
    """Monta um artefato longo, simples de filtrar por RQ e estatística."""
    rows: list[dict[str, str | float | int]] = []
    for rq, statistics, units in (
        ("RQ03", rq03_statistics, RQ03_UNITS),
        ("RQ04", rq04_statistics, RQ04_UNITS),
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
    output_dir: Path,
) -> list[Path]:
    """Gera as quatro figuras obrigatórias de RQ03 e RQ04."""
    releases = _numeric_values(dataframe, RQ03_COLUMN)
    days = _numeric_values(dataframe, RQ04_COLUMN)

    sample_releases = f"Escala original em releases; n = {len(releases):,}".replace(",", ".")
    sample_days = f"Escala original em dias; n = {len(days):,}".replace(",", ".")

    return [
        _histogram(
            releases,
            title="Distribuição do total de releases por repositório",
            subtitle=sample_releases,
            x_label="Total de releases (quantidade)",
            output_path=output_dir / "rq03_release_count_histogram.png",
        ),
        _boxplot(
            releases,
            title="Dispersão do total de releases por repositório",
            subtitle=sample_releases,
            x_label="Total de releases (quantidade)",
            output_path=output_dir / "rq03_release_count_boxplot.png",
        ),
        _histogram(
            days,
            title="Distribuição do tempo desde a última atualização",
            subtitle=sample_days,
            x_label="Dias desde o último push",
            output_path=output_dir / "rq04_days_since_update_histogram.png",
        ),
        _boxplot(
            days,
            title="Dispersão do tempo desde a última atualização",
            subtitle=sample_days,
            x_label="Dias desde o último push",
            output_path=output_dir / "rq04_days_since_update_boxplot.png",
        ),
    ]


def interpret_rq03(statistics: Mapping[str, float | int]) -> str:
    """Produz uma interpretação cautelosa da distribuição completa da RQ03."""
    return (
        f"O total típico de releases é {statistics['median']:.1f} por repositório. "
        f"A metade central está entre {statistics['q1']:.1f} e "
        f"{statistics['q3']:.1f} (IQR de {statistics['iqr']:.1f}), "
        "evidenciando forte assimetria à direita. "
        f"Há {statistics['zeros']} repositórios ({statistics['zeros'] / statistics['total'] * 100:.1f}%) "
        "sem nenhuma release formal — projetos de documentação e curadoria que não adotam esse fluxo. "
        f"Outros {statistics['at_ceiling']} repositórios atingiram o teto de "
        f"{API_RELEASE_CEILING} retornado pela API GraphQL; o valor real pode ser superior. "
        "A mediana representa melhor o caso típico do que a média, dado o grau de assimetria."
    )


def interpret_rq04(statistics: Mapping[str, float | int]) -> str:
    """Produz uma interpretação cautelosa da distribuição completa da RQ04."""
    return (
        f"A maioria dos repositórios populares foi atualizada recentemente: "
        f"a mediana é de {statistics['median']:.1f} dias desde o último push. "
        f"A metade central está entre {statistics['q1']:.1f} e {statistics['q3']:.1f} dias "
        f"(IQR de {statistics['iqr']:.1f} dias). "
        f"A média de {statistics['mean']:.1f} dias é muito superior à mediana por influência "
        f"de {statistics['above_365']} repositórios sem push há mais de um ano — "
        "projetos que acumularam popularidade no passado e hoje estão sem manutenção. "
        "Os dados foram calculados com referência à data de coleta (agosto de 2026)."
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
    rq03_statistics: Mapping[str, float | int],
    rq04_statistics: Mapping[str, float | int],
    artifacts: list[Path],
) -> None:
    """Exibe somente o resumo necessário para acompanhar a execução."""
    print("SPRINT 3 — RQ03/RQ04")
    print("\nDataset")
    print(f"- registros: {_format_number(record_count)}")

    for rq, statistics, fields in (
        (
            "RQ03",
            rq03_statistics,
            ("valid", "mean", "median", "q1", "q3", "minimum", "maximum", "zeros", "at_ceiling", "skewness"),
        ),
        (
            "RQ04",
            rq04_statistics,
            ("valid", "mean", "median", "q1", "q3", "minimum", "maximum", "zeros", "above_365", "skewness"),
        ),
    ):
        print(f"\n{rq}")
        for field in fields:
            print(f"- {field}: {_format_number(statistics[field])}")

    print("\nInterpretação RQ03")
    print(interpret_rq03(rq03_statistics))
    print("\nInterpretação RQ04")
    print(interpret_rq04(rq04_statistics))
    print("\nArtefatos gerados:")
    for artifact in artifacts:
        print(f"- {_display_path(artifact)}")


def run_analysis(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
) -> tuple[dict[str, float | int], dict[str, float | int], list[Path]]:
    """Executa a análise completa e reproduzível das RQ03/RQ04."""
    dataframe = load_dataset(input_path)
    rq03_statistics = calculate_rq03_statistics(dataframe)
    rq04_statistics = calculate_rq04_statistics(dataframe)
    summary = build_summary(rq03_statistics, rq04_statistics)
    summary_file = save_summary(summary, summary_path)
    figure_files = generate_figures(dataframe, figures_dir)
    artifacts = [summary_file, *figure_files]
    print_execution_summary(
        len(dataframe), rq03_statistics, rq04_statistics, artifacts
    )
    return rq03_statistics, rq04_statistics, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa RQ03 e RQ04 a partir do dataset validado da Sprint 2."
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
