"""Consolida RQ1, RQ2, RQ3 e inovação num único painel (Sprint 03 — Vinicius).

Execute da raiz: python -m lab02.dashboard.build_dashboard

Fontes:
  - lab02/analysis/results/rq1_resumo.csv
  - lab02/analysis/results/rq2_resumo.csv
  - lab02/analysis/results/inovacao_resumo.csv
  - lab02/analysis/results/rq3_detalhe.csv (recalculado aqui, filtrando
    apenas source_kind == "observed" — o rq3_resumo.csv "grupo" gerado por
    analyze_rq3.py inclui os 4 trials simulados do Islayder
    (SIM-S02-I21/24/25/26, source_kind == "observed_simulated") como se
    fossem dado oficial; este dashboard não usa esse resumo por esse
    motivo, e recomputa a partir do detalhe, filtrando por proveniência.

Saída: reports/figures/dashboard_final.png
"""

from __future__ import annotations

import os
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lab02-s03-mpl-cache"))
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

TREATMENTS = ("IA", "Manual")


def load_tables() -> dict[str, pd.DataFrame]:
    rq1 = pd.read_csv(RQ1_CSV)
    rq2 = pd.read_csv(RQ2_CSV)
    inovacao = pd.read_csv(INOVACAO_CSV)
    rq3_detail = pd.read_csv(RQ3_DETAIL_CSV)
    return {"rq1": rq1, "rq2": rq2, "inovacao": inovacao, "rq3_detail": rq3_detail}


def summarize_rq3_observed(rq3_detail: pd.DataFrame) -> pd.DataFrame:
    """Recalcula LOC/CC/duplicação usando apenas trials source_kind=='observed'.

    O rq3_resumo.csv produzido por analyze_rq3.py mistura os trials reais com
    os quatro cenários sintéticos do Islayder (observed_simulated); esta
    função ignora esse arquivo e recomputa a partir do detalhe já filtrado.
    """
    observed = rq3_detail.loc[rq3_detail.source_kind == "observed"].copy()
    rows = []
    for treatment in TREATMENTS:
        group = observed.loc[observed.tratamento == treatment]
        for column, label in (
            ("loc", "LOC lógico (lloc)"),
            ("avg_cyclomatic_complexity", "Complexidade ciclomática média"),
            ("duplication_percentage", "Duplicação (%)"),
        ):
            values = group[column].dropna()
            rows.append(
                {
                    "tratamento": treatment,
                    "metrica": column,
                    "unidade": label,
                    "n": len(values),
                    "mediana": values.median() if not values.empty else None,
                }
            )
    return pd.DataFrame(rows), observed


def data_composition_note(rq3_detail: pd.DataFrame) -> str:
    counts = rq3_detail.source_kind.value_counts().to_dict()
    participantes_observed = sorted(
        rq3_detail.loc[rq3_detail.source_kind == "observed", "participante"].unique()
    )
    return (
        f"Composição dos dados (RQ3, n={len(rq3_detail)} trials no CSV bruto): "
        f"observed={counts.get('observed', 0)} · "
        f"observed_simulated={counts.get('observed_simulated', 0)} · "
        f"agent_delegated_codex_work={counts.get('agent_delegated_codex_work', 0)}.  "
        f"Este dashboard usa somente source_kind='observed' "
        f"(participante(s): {', '.join(participantes_observed) or 'nenhum'}). "
        "Islayder (SIM-*) é cenário sintético declarado; Fernanda ainda sem "
        "snapshot/execução humana completa — pendente para as próximas versões."
    )


def bar_with_labels(ax, values: dict[str, float], ylabel: str, title: str, fmt: str = "{:.2f}") -> None:
    treatments = list(values.keys())
    heights = list(values.values())
    colors = [COLORS[t] for t in treatments]
    bars = ax.bar(treatments, heights, color=colors, width=0.55)
    for bar, height in zip(bars, heights):
        ax.annotate(
            fmt.format(height) if height is not None else "n/a",
            (bar.get_x() + bar.get_width() / 2, height if height is not None else 0),
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
    rq1, rq2, inovacao = tables["rq1"], tables["rq2"], tables["inovacao"]
    rq3_summary, rq3_observed = summarize_rq3_observed(tables["rq3_detail"])

    fig, axes = plt.subplots(2, 3, figsize=(15, 9))

    # 1. Tempo (RQ1) — mediana em minutos
    tempo = {row.tratamento: row.mediana_min for row in rq1.itertuples()}
    bar_with_labels(axes[0, 0], tempo, "Minutos (mediana)", "RQ1 — Tempo até green", fmt="{:.2f} min")

    # 2. Taxa de sucesso final (RQ2)
    taxa = {row.tratamento: row.taxa_final_mediana_pct for row in rq2.itertuples()}
    bar_with_labels(axes[0, 1], taxa, "Testes passando (%)", "RQ2 — Taxa final de sucesso", fmt="{:.1f}%")
    axes[0, 1].set_ylim(0, 110)

    # 3. Ciclos até green (inovação)
    ciclos = {row.tratamento: row.ciclos_mediana for row in inovacao.itertuples()}
    bar_with_labels(axes[0, 2], ciclos, "Ciclos (mediana)", "Inovação — Ciclos até green", fmt="{:.1f}")

    # 4. LOC (RQ3, observed)
    loc = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[rq3_summary.metrica == "loc"].itertuples()
    }
    bar_with_labels(axes[1, 0], loc, "LOC (mediana)", "RQ3 — LOC lógico", fmt="{:.1f}")

    # 5. Complexidade ciclomática (RQ3, observed)
    cc = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[rq3_summary.metrica == "avg_cyclomatic_complexity"].itertuples()
    }
    bar_with_labels(axes[1, 1], cc, "CC média (mediana)", "RQ3 — Complexidade ciclomática", fmt="{:.2f}")

    # 6. Duplicação (RQ3, observed)
    dup = {
        row.tratamento: row.mediana
        for row in rq3_summary.loc[rq3_summary.metrica == "duplication_percentage"].itertuples()
    }
    bar_with_labels(axes[1, 2], dup, "Duplicação % (mediana)", "RQ3 — Duplicação de código", fmt="{:.1f}%")
    axes[1, 2].set_ylim(0, max(1.0, max(v for v in dup.values() if v is not None) * 1.3))

    n_observed = int((tables["rq3_detail"].source_kind == "observed").sum())
    participantes = sorted(
        tables["rq3_detail"].loc[tables["rq3_detail"].source_kind == "observed", "participante"].unique()
    )
    fig.suptitle(
        f"Lab02 — Dashboard consolidado (Sprint 03)\n"
        f"n={n_observed} trials observados · participante(s): {', '.join(participantes)}",
        fontsize=13,
        fontweight="bold",
    )
    fig.text(0.5, 0.01, data_composition_note(tables["rq3_detail"]), ha="center", fontsize=7.5, wrap=True, color="#444444")
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