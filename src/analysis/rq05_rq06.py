"""Análise estatística e visualização das RQ05 e RQ06 da Sprint 3."""

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
    PROJECT_ROOT / "data" / "processed" / "s03" / "rq05_rq06_summary.csv"
)
DEFAULT_FIGURES_DIR = PROJECT_ROOT / "reports" / "figures" / "s03"

RQ05_COLUMN = "primary_language"
RQ06_COLUMN = "closed_issues_ratio"
TOTAL_ISSUES_COLUMN = "total_issues"
REQUIRED_COLUMNS = (RQ05_COLUMN, RQ06_COLUMN, TOTAL_ISSUES_COLUMN)

LANGUAGE_NOT_INFORMED = "Não informado"
TOP_LANGUAGES_LIMIT = 15

# Fonte de referência para popularidade de linguagens (fixada desde a Sprint 2
# e mantida ao longo de todo o Lab01, inclusive na RQ07).
# TIOBE Software. TIOBE Index — agosto de 2026. https://www.tiobe.com/tiobe-index/
TIOBE_TOP_10 = [
    "Python",
    "C",
    "C++",
    "Java",
    "C#",
    "JavaScript",
    "Visual Basic",
    "SQL",
    "R",
    "Rust",
]

RQ06_UNITS = {
    "total": "records",
    "valid": "records",
    "missing": "records",
    "undefined_zero_issues": "records",
    "minimum": "ratio",
    "maximum": "ratio",
    "mean": "ratio",
    "median": "ratio",
    "standard_deviation": "ratio",
    "q1": "ratio",
    "q3": "ratio",
    "iqr": "ratio",
    "p10": "ratio",
    "p90": "ratio",
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


def _closed_issues_ratio_values(dataframe: pd.DataFrame) -> pd.Series:
    """Converte a razão de issues fechadas, preservando valores indefinidos como NaN."""
    if RQ06_COLUMN not in dataframe.columns:
        raise ValueError(f"Coluna obrigatória ausente: {RQ06_COLUMN}")
    numeric = pd.to_numeric(dataframe[RQ06_COLUMN], errors="coerce")
    valid = numeric.dropna().astype(float)
    if valid.empty:
        raise ValueError(f"A coluna {RQ06_COLUMN} não contém valores válidos.")
    if ((valid < 0) | (valid > 1)).any():
        raise ValueError(f"A coluna {RQ06_COLUMN} contém valor(es) fora de 0-1.")
    return numeric


def calculate_rq05_statistics(dataframe: pd.DataFrame) -> dict[str, object]:
    """Calcula a distribuição de frequência da linguagem primária."""
    if RQ05_COLUMN not in dataframe.columns:
        raise ValueError(f"Coluna obrigatória ausente: {RQ05_COLUMN}")
    languages = dataframe[RQ05_COLUMN].fillna(LANGUAGE_NOT_INFORMED)
    total = int(len(dataframe))
    counts = languages.value_counts()
    not_informed_count = int(counts.get(LANGUAGE_NOT_INFORMED, 0))
    top_languages = [
        {
            "language": str(language),
            "count": int(count),
            "percentage": float(count) / total * 100 if total else 0.0,
        }
        for language, count in counts.head(TOP_LANGUAGES_LIMIT).items()
    ]
    tiobe_top_10_count = int(
        languages.isin(TIOBE_TOP_10).sum()
    )
    return {
        "total": total,
        "unique_languages": int(counts.shape[0]),
        "not_informed_count": not_informed_count,
        "not_informed_percentage": (
            not_informed_count / total * 100 if total else 0.0
        ),
        "top_languages": top_languages,
        "tiobe_top_10_count": tiobe_top_10_count,
        "tiobe_top_10_percentage": (
            tiobe_top_10_count / total * 100 if total else 0.0
        ),
    }


def calculate_rq06_statistics(dataframe: pd.DataFrame) -> dict[str, float | int]:
    """Calcula a distribuição da razão de issues fechadas."""
    raw = _closed_issues_ratio_values(dataframe)
    valid = raw.dropna().astype(float)
    total = int(len(dataframe))
    valid_count = int(valid.count())
    total_issues = pd.to_numeric(
        dataframe[TOTAL_ISSUES_COLUMN], errors="coerce"
    )
    undefined_zero_issues = int(
        ((total_issues == 0) & raw.isna()).sum()
    )
    q1 = float(valid.quantile(0.25))
    q3 = float(valid.quantile(0.75))
    return {
        "total": total,
        "valid": valid_count,
        "missing": total - valid_count,
        "undefined_zero_issues": undefined_zero_issues,
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


def build_summary(
    rq05_statistics: Mapping[str, object],
    rq06_statistics: Mapping[str, float | int],
) -> pd.DataFrame:
    """Monta um artefato longo, simples de filtrar por RQ e estatística."""
    rows: list[dict[str, str | float | int]] = []
    for key, value in rq05_statistics.items():
        if key == "top_languages":
            for entry in value:
                rows.append(
                    {
                        "rq": "RQ05",
                        "statistic": f"top_language::{entry['language']}",
                        "value": entry["count"],
                        "unit": "records",
                    }
                )
            continue
        unit = "percent" if "percentage" in key else "records" if "count" in key or key == "total" else "records"
        rows.append({"rq": "RQ05", "statistic": key, "value": value, "unit": unit})
    for statistic, value in rq06_statistics.items():
        rows.append(
            {
                "rq": "RQ06",
                "statistic": statistic,
                "value": value,
                "unit": RQ06_UNITS[statistic],
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


def _format_percent_axis(value: float, _position: int) -> str:
    return f"{value * 100:.0f}%"


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


def generate_rq05_figure(
    rq05_statistics: Mapping[str, object],
    output_path: Path,
) -> Path:
    """Gera gráfico de barras ranqueado com o top 15 de linguagens primárias."""
    top_languages = list(rq05_statistics["top_languages"])  # type: ignore[index]
    labels = [entry["language"] for entry in reversed(top_languages)]
    values = [entry["count"] for entry in reversed(top_languages)]

    fig, ax = plt.subplots(figsize=(10, 7))
    _prepare_axes(ax)
    bars = ax.barh(labels, values, color=BLUE, edgecolor=BLUE_DARK, linewidth=0.8)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_width() + max(values) * 0.01,
            bar.get_y() + bar.get_height() / 2,
            f"{value:,}".replace(",", "."),
            va="center",
            fontsize=9,
            color=CHARCOAL,
        )
    ax.set_xlabel(
        "Número de repositórios", fontsize=11, color=CHARCOAL, labelpad=9
    )
    ax.xaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    sample_note = (
        f"n = {rq05_statistics['total']:,}".replace(",", ".")
        + f"; {rq05_statistics['unique_languages']} linguagens distintas"
    )
    fig.suptitle(
        "Top 15 linguagens primárias — repositórios populares",
        fontsize=16,
        fontweight="bold",
        color=CHARCOAL,
        y=0.98,
    )
    ax.set_title(sample_note, fontsize=10.5, color="#4B5563", pad=12)
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    return _save_figure(fig, output_path)


def _histogram(
    values: pd.Series,
    *,
    title: str,
    subtitle: str,
    x_label: str,
    output_path: Path,
    percent_axis: bool = False,
) -> Path:
    fig, ax = plt.subplots(figsize=(10, 6))
    _prepare_axes(ax)
    ax.hist(values, bins="auto", color=BLUE, edgecolor=BLUE_DARK, linewidth=0.7)
    ax.set_xlabel(x_label, fontsize=11, color=CHARCOAL, labelpad=9)
    ax.set_ylabel("Número de repositórios", fontsize=11, color=CHARCOAL, labelpad=9)
    if percent_axis:
        ax.xaxis.set_major_formatter(FuncFormatter(_format_percent_axis))
    else:
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
    percent_axis: bool = False,
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
    if percent_axis:
        ax.xaxis.set_major_formatter(FuncFormatter(_format_percent_axis))
    else:
        ax.xaxis.set_major_formatter(FuncFormatter(_format_thousands))
    ax.grid(axis="x", color=GRID, linewidth=0.7, alpha=0.7)
    ax.set_axisbelow(True)
    fig.suptitle(title, fontsize=16, fontweight="bold", color=CHARCOAL, y=0.98)
    ax.set_title(subtitle, fontsize=10.5, color="#4B5563", pad=12)
    fig.tight_layout(rect=(0, 0, 1, 0.91))
    return _save_figure(fig, output_path)


def generate_figures(
    dataframe: pd.DataFrame,
    rq05_statistics: Mapping[str, object],
    output_dir: Path,
) -> list[Path]:
    """Gera as três figuras: ranking de linguagens, histograma e boxplot de RQ06."""
    ratio = _closed_issues_ratio_values(dataframe).dropna().astype(float)
    sample_ratio = (
        f"Escala de proporção (0-1); n = {len(ratio):,}".replace(",", ".")
    )
    return [
        generate_rq05_figure(
            rq05_statistics,
            output_dir / "rq05_language_ranking.png",
        ),
        _histogram(
            ratio,
            title="Distribuição da razão de issues fechadas",
            subtitle=sample_ratio,
            x_label="Razão de issues fechadas",
            output_path=output_dir / "rq06_closed_ratio_histogram.png",
            percent_axis=True,
        ),
        _boxplot(
            ratio,
            title="Boxplot da razão de issues fechadas",
            subtitle=sample_ratio,
            x_label="Razão de issues fechadas",
            output_path=output_dir / "rq06_closed_ratio_boxplot.png",
            percent_axis=True,
        ),
    ]


def interpret_rq05(statistics: Mapping[str, object]) -> str:
    """Produz uma interpretação cautelosa da distribuição de linguagens."""
    top_languages = list(statistics["top_languages"])  # type: ignore[index]
    top_3 = top_languages[:3]
    top_3_share = sum(entry["percentage"] for entry in top_3)
    top_3_names = ", ".join(entry["language"] for entry in top_3)
    total_formatted = f"{statistics['total']:,}".replace(",", ".")
    tiobe_count_formatted = f"{statistics['tiobe_top_10_count']:,}".replace(",", ".")
    return (
        f"Foram identificadas {statistics['unique_languages']} linguagens distintas "
        f"entre os {total_formatted} repositórios, com "
        f"{statistics['not_informed_count']} "
        f"({statistics['not_informed_percentage']:.1f}%) sem linguagem primária "
        f"informada. As três linguagens mais frequentes ({top_3_names}) respondem "
        f"por {top_3_share:.1f}% da amostra. Comparando com o TIOBE Index de "
        f"agosto/2026, {tiobe_count_formatted} repositórios "
        f"({statistics['tiobe_top_10_percentage']:.1f}%) estão em linguagens do "
        "top 10 do índice — os dados sugerem concentração parcial nas linguagens "
        "mais populares em geral, mas com divergências notáveis em linguagens "
        "fortes no GitHub que não aparecem no top 10 do TIOBE."
    )


def interpret_rq06(statistics: Mapping[str, float | int]) -> str:
    """Produz uma interpretação cautelosa da distribuição de RQ06."""
    return (
        f"A razão típica de issues fechadas é de {statistics['median']:.1%}, "
        f"com a metade central da amostra entre {statistics['q1']:.1%} e "
        f"{statistics['q3']:.1%} (IQR de {statistics['iqr']:.1%}). "
        f"O mínimo observado foi {statistics['minimum']:.1%} e o máximo "
        f"{statistics['maximum']:.1%}, indicando dispersão relevante mesmo "
        "dentro dos repositórios populares. "
        f"Foram identificados {statistics['undefined_zero_issues']} "
        "repositórios sem nenhuma issue, tratados como razão indefinida "
        "(não computados nesta distribuição). Os dados sugerem que "
        "repositórios populares concentram, em geral, taxas altas de "
        "fechamento de issues, mas existe uma cauda de projetos com taxas "
        "bem abaixo da mediana."
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
    rq05_statistics: Mapping[str, object],
    rq06_statistics: Mapping[str, float | int],
    artifacts: list[Path],
) -> None:
    """Exibe somente o resumo necessário para acompanhar a execução."""
    print("SPRINT 3 — RQ05/RQ06")
    print("\nDataset")
    print(f"- registros: {_format_number(record_count)}")

    print("\nRQ05 — top 10 linguagens")
    for entry in list(rq05_statistics["top_languages"])[:10]:  # type: ignore[index]
        print(
            f"- {entry['language']}: {_format_number(entry['count'])} "
            f"({entry['percentage']:.2f}%)"
        )
    print(f"- linguagens distintas: {rq05_statistics['unique_languages']}")
    print(
        "- não informado: "
        f"{_format_number(rq05_statistics['not_informed_count'])} "
        f"({rq05_statistics['not_informed_percentage']:.2f}%)"
    )
    print(
        "- no TIOBE top 10: "
        f"{_format_number(rq05_statistics['tiobe_top_10_count'])} "
        f"({rq05_statistics['tiobe_top_10_percentage']:.2f}%)"
    )

    print("\nRQ06")
    for field in ("valid", "undefined_zero_issues", "mean", "median", "q1", "q3", "minimum", "maximum", "skewness"):
        print(f"- {field}: {_format_number(rq06_statistics[field])}")

    print("\nInterpretação RQ05")
    print(interpret_rq05(rq05_statistics))
    print("\nInterpretação RQ06")
    print(interpret_rq06(rq06_statistics))

    print("\nArtefatos gerados:")
    for artifact in artifacts:
        print(f"- {_display_path(artifact)}")


def run_analysis(
    *,
    input_path: Path = DEFAULT_INPUT_PATH,
    summary_path: Path = DEFAULT_SUMMARY_PATH,
    figures_dir: Path = DEFAULT_FIGURES_DIR,
) -> tuple[dict[str, object], dict[str, float | int], list[Path]]:
    """Executa a análise completa e reproduzível das RQ05/RQ06."""
    dataframe = load_dataset(input_path)
    rq05_statistics = calculate_rq05_statistics(dataframe)
    rq06_statistics = calculate_rq06_statistics(dataframe)
    summary = build_summary(rq05_statistics, rq06_statistics)
    summary_file = save_summary(summary, summary_path)
    figure_files = generate_figures(dataframe, rq05_statistics, figures_dir)
    artifacts = [summary_file, *figure_files]
    print_execution_summary(
        len(dataframe), rq05_statistics, rq06_statistics, artifacts
    )
    return rq05_statistics, rq06_statistics, artifacts


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Analisa RQ05 e RQ06 a partir do dataset validado da Sprint 2."
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
