"""Audita os CSVs da S02 e gera a análise parcial da Sprint 03.

Execute da raiz: python -m lab02.analysis.analyze_rq1_rq2
As exclusões abaixo vêm dos relatórios individuais da S02, não de um limiar
escolhido depois de observar os resultados. Novos trials válidos entram sem
alterar a lista de exclusões.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path

os.environ.setdefault("MPLCONFIGDIR", str(Path(tempfile.gettempdir()) / "lab02-s03-mpl-cache"))
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from lab02.trials.config import (
    BASE_DIR,
    CYCLES_CSV,
    FERNANDA_ALLOCATION,
    ISLAYDER_ALLOCATION,
    TIME_BOX_SECONDS,
    TRIALS_CSV,
)

RESULTS_DIR = BASE_DIR / "lab02" / "analysis" / "results"
FIGURES_DIR = BASE_DIR / "reports" / "figures"
VALID_PARTICIPANTS = {"Islayder", "Fernanda", "Vinicius"}
VALID_KATAS = set(ISLAYDER_ALLOCATION)
ISSUES = {
    "Islayder": {1: "#21", 2: "#24", 3: "#25", 4: "#26"},
    "Fernanda": {1: "#27", 2: "#19", 3: "#28", 4: "#29"},
    "Vinicius": {1: "#22", 2: "#30", 3: "#31", 4: "#32"},
}
# Incidentes documentados em reports/sprints/lab02_s02/{vinicius,fernanda}.md.
DOCUMENTED_EXCLUSIONS = {
    "c825af06fdf34b8383348801c0fc5782": "interrompido; tentativa descartada (#1)",
    "8eee3cfc8eee49c98e5607ee320113bd": "time-box de processo residual; tentativa descartada (#22)",
    "5e85c97fc84f4819a10aa87970316abf": "ensaio do instrumento, sem tempo humano válido (Fernanda)",
    "31c7f16ce79c478ab8f81cd8628e6e3c": "ensaio do instrumento, sem tempo humano válido (Fernanda)",
    "bd057b8dcaef41a6a9503c053b9d57f3": "ensaio do instrumento, sem tempo humano válido (Fernanda)",
    "4dfbe8c44c964a65ae003d35d6a60754": "ensaio do instrumento, sem tempo humano válido (Fernanda)",
}
TRIAL_COLUMNS = {
    "trial_id", "issue", "participante", "kata", "tratamento", "tempo_segundos",
    "testes_passando", "testes_falhando", "total_testes", "taxa_sucesso",
    "ciclos", "status", "codigo_path", "iniciado_em", "finalizado_em", "source_kind",
}
CYCLE_COLUMNS = {
    "trial_id", "issue", "participante", "kata", "tratamento", "ciclo",
    "tempo_segundos", "testes_passando", "testes_falhando", "total_testes",
    "taxa_sucesso", "source_kind",
}
COLORS = {"IA": "#176b9a", "Manual": "#cb6c28"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def number(value: str, name: str, trial_id: str) -> float:
    require(value != "", f"{trial_id}: valor ausente em {name}")
    result = float(value)
    require(pd.notna(result) and result != float("inf") and result != -float("inf"),
            f"{trial_id}: valor inválido em {name}")
    return result


def integer(value: str, name: str, trial_id: str) -> int:
    result = number(value, name, trial_id)
    require(result.is_integer(), f"{trial_id}: {name} não é inteiro")
    return int(result)


def check_tests(row: pd.Series, trial_id: str) -> None:
    passed = integer(row.testes_passando, "testes_passando", trial_id)
    failed = integer(row.testes_falhando, "testes_falhando", trial_id)
    total = integer(row.total_testes, "total_testes", trial_id)
    rate = number(row.taxa_sucesso, "taxa_sucesso", trial_id)
    require(total > 0 and passed >= 0 and failed >= 0 and passed + failed == total,
            f"{trial_id}: contagens de testes inconsistentes")
    require(abs(rate - 100 * passed / total) <= 0.02,
            f"{trial_id}: taxa de sucesso inconsistente")


def load_and_audit() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trials = pd.read_csv(TRIALS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    cycles = pd.read_csv(CYCLES_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    require(TRIAL_COLUMNS <= set(trials), "trials.csv: colunas obrigatórias ausentes")
    require(CYCLE_COLUMNS <= set(cycles), "trial_cycles.csv: colunas obrigatórias ausentes")
    require(not trials.trial_id.duplicated().any(), "trial_id duplicado em trials.csv")
    require(not cycles.duplicated(["trial_id", "ciclo"]).any(),
            "par (trial_id, ciclo) duplicado em trial_cycles.csv")
    require(set(cycles.trial_id) == set(trials.trial_id),
            "trial_id órfão ou sem ciclos entre os CSVs")
    audit_rows = []
    for _, trial in trials.iterrows():
        tid = trial.trial_id
        source = trial.source_kind
        missing = [field for field in ("trial_id", "issue", "participante", "kata",
                                      "tratamento", "tempo_segundos", "testes_passando",
                                      "testes_falhando", "total_testes", "taxa_sucesso",
                                      "ciclos", "status", "source_kind") if not trial[field]]
        require(not missing, f"{tid}: campos obrigatórios ausentes: {missing}")
        require(
            source in {
                "observed",
                "observed_simulated",
                "agent_delegated_codex_work",
            },
            f"{tid}: origem inválida",
        )
        require(trial.participante in VALID_PARTICIPANTS, f"{tid}: participante inválido")
        require(trial.kata in VALID_KATAS, f"{tid}: kata inválido")
        require(trial.tratamento in {"IA", "Manual"}, f"{tid}: tratamento inválido")
        require(re.fullmatch(r"#[1-9][0-9]*", trial.issue) is not None,
                f"{tid}: Issue inválida")
        kata_num = int(re.match(r"kata([1-4])_", trial.kata).group(1))
        expected_treatment = (FERNANDA_ALLOCATION if trial.participante == "Fernanda"
                              else ISLAYDER_ALLOCATION)[trial.kata]
        require(trial.tratamento == expected_treatment, f"{tid}: tratamento fora da matriz")
        if source in {"observed", "agent_delegated_codex_work"}:
            require(trial.iniciado_em != "" and trial.finalizado_em != "",
                    f"{tid}: timestamps de execução ausentes")
            started = pd.to_datetime(trial.iniciado_em, utc=True)
            finished = pd.to_datetime(trial.finalizado_em, utc=True)
            require(finished >= started, f"{tid}: timestamps invertidos")
            require(re.fullmatch(r"[0-9a-f]{32}", tid) is not None,
                    f"{tid}: trial_id observado inválido")
            require(trial.status in {"green", "time-box", "interrupted", "error"},
                    f"{tid}: status inválido")
            require(Path(trial.codigo_path).as_posix()
                    == f"lab02/trials/results/solutions/{tid}/solucao.py",
                    f"{tid}: snapshot não corresponde ao trial_id")
            require(trial.codigo_path != "" and (BASE_DIR / trial.codigo_path).is_file(),
                    f"{tid}: snapshot ausente")
            require(trial.issue == ISSUES[trial.participante][kata_num]
                    or tid in DOCUMENTED_EXCLUSIONS,
                    f"{tid}: Issue não corresponde ao participante/kata")
        else:
            require(tid.startswith("SIM-") and trial.status.startswith("simulated-"),
                    f"{tid}: simulação sem identificação consistente")
            require(trial.codigo_path == "", f"{tid}: simulação aponta para snapshot")
        elapsed = number(trial.tempo_segundos, "tempo_segundos", tid)
        require(0 <= elapsed <= TIME_BOX_SECONDS, f"{tid}: tempo fora do time-box")
        check_tests(trial, tid)
        trial_cycles = cycles.loc[cycles.trial_id == tid].copy()
        trial_cycles["ciclo_num"] = trial_cycles.ciclo.map(lambda v: integer(v, "ciclo", tid))
        trial_cycles = trial_cycles.sort_values("ciclo_num")
        count = integer(trial.ciclos, "ciclos", tid)
        require(count > 0 and list(trial_cycles.ciclo_num) == list(range(1, count + 1)),
                f"{tid}: ciclos ausentes ou não sequenciais")
        prev_time = -1.0
        for _, cycle in trial_cycles.iterrows():
            require(cycle.source_kind == source, f"{tid}: origem divergente entre CSVs")
            for field in ("issue", "participante", "kata", "tratamento"):
                require(cycle[field] == trial[field], f"{tid}: {field} divergente no ciclo")
            check_tests(cycle, tid)
            cycle_time = number(cycle.tempo_segundos, "tempo_segundos do ciclo", tid)
            require(prev_time <= cycle_time <= elapsed + 0.02,
                    f"{tid}: tempos dos ciclos inconsistentes")
            prev_time = cycle_time
        last = trial_cycles.iloc[-1]
        for field in ("testes_passando", "testes_falhando", "total_testes"):
            require(integer(trial[field], field, tid) == integer(last[field], field, tid),
                    f"{tid}: resultado final difere do último ciclo")
        if source in {"observed", "agent_delegated_codex_work"}:
            if trial.status == "green":
                require(integer(trial.testes_falhando, "testes_falhando", tid) == 0,
                        f"{tid}: green com falhas")
            if trial.status == "time-box":
                require(elapsed == TIME_BOX_SECONDS, f"{tid}: time-box sem censura em 35 min")
        if source == "observed_simulated":
            decision, reason = "excluído", "cenário simulado; sem execução humana"
        elif tid in DOCUMENTED_EXCLUSIONS:
            decision, reason = "excluído", DOCUMENTED_EXCLUSIONS[tid]
        elif trial.status in {"interrupted", "error"}:
            decision, reason = "excluído", f"status {trial.status}; trial incompleto"
        elif source == "agent_delegated_codex_work":
            decision, reason = "incluído", "execução delegada ao Codex Work"
        else:
            decision, reason = "incluído", "observado e sem incidente documentado"
        audit_rows.append({
            "trial_id": tid, "issue": trial.issue, "participante": trial.participante,
            "kata": trial.kata, "tratamento": trial.tratamento,
            "source_kind": source, "status": trial.status,
            "tempo_segundos": elapsed, "ciclos": count,
            "campos_obrigatorios_ausentes": 0,
            "decisao": decision, "motivo": reason,
        })
    audit = pd.DataFrame(audit_rows)
    included = trials.loc[trials.trial_id.isin(audit.loc[audit.decisao == "incluído", "trial_id"])].copy()
    require(not included.empty, "nenhum trial elegível para análise")
    require(not included.issue.duplicated().any(), "Issue duplicada entre trials incluídos")
    require(not included.duplicated(["participante", "kata"]).any(),
            "participante/kata duplicado entre trials incluídos")
    included_cycles = cycles.loc[cycles.trial_id.isin(included.trial_id)].copy()
    for frame in (included, included_cycles):
        for field in ("tempo_segundos", "testes_passando", "testes_falhando",
                      "total_testes", "taxa_sucesso", "ciclos", "ciclo"):
            if field in frame:
                frame[field] = pd.to_numeric(frame[field])
    return audit, included, included_cycles


def analyze(audit: pd.DataFrame, trials: pd.DataFrame, cycles: pd.DataFrame) -> dict[str, pd.DataFrame]:
    rq1_rows = []
    rq2_rows = []
    for treatment in ("IA", "Manual"):
        group = trials.loc[trials.tratamento == treatment]
        times = group.tempo_segundos / 60
        q1, q3 = times.quantile([0.25, 0.75])
        rq1_rows.append({
            "tratamento": treatment, "n_trials": len(group),
            "n_participantes": group.participante.nunique(),
            "green": int((group.status == "green").sum()),
            "censurados_35min": int((group.status == "time-box").sum()),
            "mediana_min": times.median(), "q1_min": q1, "q3_min": q3,
            "iqr_min": q3 - q1,
        })
        rq2_rows.append({
            "tratamento": treatment, "n_trials": len(group),
            "green": int((group.status == "green").sum()),
            "time_box": int((group.status == "time-box").sum()),
            "passed_soma": int(group.testes_passando.sum()),
            "failed_soma": int(group.testes_falhando.sum()),
            "total_testes_soma": int(group.total_testes.sum()),
            "taxa_final_mediana_pct": group.taxa_sucesso.median(),
            "taxa_final_media_pct": group.taxa_sucesso.mean(),
            "falhas_finais_mediana": group.testes_falhando.median(),
        })
    rq1 = pd.DataFrame(rq1_rows)
    rq2 = pd.DataFrame(rq2_rows)
    detail = trials[["trial_id", "issue", "participante", "kata", "tratamento",
                     "status", "tempo_segundos", "testes_passando", "testes_falhando",
                     "total_testes", "taxa_sucesso", "ciclos"]].copy()
    detail["tempo_min"] = detail.tempo_segundos / 60
    detail["censurado_35min"] = detail.status.eq("time-box")
    detail = detail.sort_values(["participante", "kata"])
    paired = []
    for participant, group in trials.groupby("participante"):
        if (len(group) == 4 and group.kata.nunique() == 4
                and (group.tratamento.value_counts().reindex(["IA", "Manual"], fill_value=0) == 2).all()):
            paired.append({"participante": participant,
                           "mediana_ia_min": group.loc[group.tratamento == "IA", "tempo_segundos"].median() / 60,
                           "mediana_manual_min": group.loc[group.tratamento == "Manual", "tempo_segundos"].median() / 60})
    pairs = pd.DataFrame(paired, columns=["participante", "mediana_ia_min", "mediana_manual_min"])
    test = {"variavel": "mediana por participante dos 2 tempos IA vs 2 Manual (min)",
            "n_pares": len(pairs), "estatistica_w": "", "p_value": "",
            "aplicado": False, "motivo": ""}
    if trials.status.eq("time-box").any():
        test["motivo"] = "há censura; Wilcoxon pareado não modela tempo até green censurado"
    elif len(pairs) < 2:
        test["motivo"] = "menos de 2 participantes com os quatro katas e 2 trials por tratamento"
    else:
        from scipy.stats import wilcoxon

        difference = pairs.mediana_ia_min - pairs.mediana_manual_min
        if (difference == 0).all():
            test["motivo"] = "todas as diferenças pareadas são zero"
        else:
            result = wilcoxon(pairs.mediana_ia_min, pairs.mediana_manual_min,
                              alternative="two-sided", method="auto")
            test.update({"estatistica_w": result.statistic, "p_value": result.pvalue,
                         "aplicado": True, "motivo": "pares formados por participante; katas diferentes em cada tratamento"})
    evolution_rows = []
    for _, trial in trials.iterrows():
        current = cycles.loc[cycles.trial_id == trial.trial_id].sort_values("ciclo")
        first = current.iloc[0]
        green = current.loc[(current.testes_falhando == 0) & (current.testes_passando == current.total_testes)]
        evolution_rows.append({
            "trial_id": trial.trial_id, "participante": trial.participante,
            "kata": trial.kata, "tratamento": trial.tratamento,
            "n_ciclos": len(current), "primeiro_ciclo_min": first.tempo_segundos / 60,
            "primeiro_passed": int(first.testes_passando),
            "primeiro_failed": int(first.testes_falhando),
            "primeira_taxa_pct": first.taxa_sucesso,
            "ultimo_ciclo_min": current.iloc[-1].tempo_segundos / 60,
            "ultima_taxa_pct": current.iloc[-1].taxa_sucesso,
            "ciclo_ate_green": int(green.iloc[0].ciclo) if not green.empty else "",
            "censurado_35min": trial.status == "time-box",
        })
    evolution = pd.DataFrame(evolution_rows).sort_values(["participante", "kata"])
    innovation = evolution.groupby("tratamento", sort=False).agg(
        n_trials=("trial_id", "size"),
        ciclos_mediana=("n_ciclos", "median"),
        ciclos_min=("n_ciclos", "min"), ciclos_max=("n_ciclos", "max"),
        taxa_primeiro_ciclo_mediana_pct=("primeira_taxa_pct", "median"),
        taxa_ultimo_ciclo_mediana_pct=("ultima_taxa_pct", "median"),
    ).reset_index()
    return {"auditoria_trials": audit, "rq1_resumo": rq1,
            "rq1_detalhe": detail, "rq1_pares": pairs,
            "rq1_wilcoxon": pd.DataFrame([test]), "rq2_resumo": rq2,
            "inovacao_detalhe": evolution, "inovacao_resumo": innovation}


def make_figures(trials: pd.DataFrame, cycles: pd.DataFrame, tables: dict[str, pd.DataFrame]) -> None:
    plt.rcParams.update({"font.size": 10, "figure.dpi": 140})
    # Cada ponto representa um trial; a linha mostra a mediana, sem sugerir
    # precisão estatística que dois pontos por tratamento não têm.
    fig, ax = plt.subplots(figsize=(8, 5))
    for x, treatment in enumerate(("IA", "Manual")):
        group = trials.loc[trials.tratamento == treatment].sort_values("kata")
        offsets = pd.Series(range(len(group)), index=group.index) * 0.13 - 0.065 * (len(group) - 1)
        for idx, row in group.iterrows():
            marker = "x" if row.status == "time-box" else "o"
            ax.scatter(x + offsets[idx], row.tempo_segundos / 60, color=COLORS[treatment],
                       marker=marker, s=70)
            ax.annotate(f"K{row.kata[4]} · {row.participante}",
                        (x + offsets[idx], row.tempo_segundos / 60),
                        xytext=(5, 5), textcoords="offset points", fontsize=8)
        median = group.tempo_segundos.median() / 60
        ax.hlines(median, x - 0.25, x + 0.25, colors=COLORS[treatment], linewidth=2,
                  label=f"Mediana {treatment}: {median:.2f} min")
    ax.set(xlim=(-0.55, 1.55), xticks=[0, 1], xticklabels=["IA", "Manual"],
           ylabel="Tempo observado ou limite (min)",
           title="RQ1 — tempo por trial e mediana por tratamento")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(loc="upper left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "rq1_tempo_ia_vs_manual.png")
    plt.close(fig)

    evolution = tables["inovacao_detalhe"]
    fig, ax = plt.subplots(figsize=(8, 5))
    for x, treatment in enumerate(("IA", "Manual")):
        group = evolution.loc[evolution.tratamento == treatment].sort_values("kata")
        for i, (_, row) in enumerate(group.iterrows()):
            xpos = x + (i - (len(group) - 1) / 2) * 0.18
            if row.n_ciclos == 1:
                ax.scatter(xpos, row.ultima_taxa_pct, color=COLORS[treatment], s=55)
            else:
                ax.plot([xpos - 0.035, xpos + 0.035],
                        [row.primeira_taxa_pct, row.ultima_taxa_pct],
                        color=COLORS[treatment], marker="o", linewidth=1.4)
            ax.annotate(f"K{row.kata[4]}", (xpos, row.ultima_taxa_pct),
                        xytext=(3, 5), textcoords="offset points", fontsize=8)
    ax.set(xlim=(-0.5, 1.5), ylim=(-5, 112), xticks=[0, 1],
           xticklabels=["IA", "Manual"], ylabel="Testes passando (%)",
           title="RQ2 — taxa no primeiro e último ciclo por trial")
    ax.grid(axis="y", alpha=0.25)
    fig.text(0.5, 0.01, "Ponto = um ciclo; linha = primeiro ao último ciclo; K = kata.",
             ha="center", fontsize=8)
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    fig.savefig(FIGURES_DIR / "rq2_testes_ia_vs_manual.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(9, 5))
    for _, trial in trials.sort_values(["tratamento", "kata"]).iterrows():
        current = cycles.loc[cycles.trial_id == trial.trial_id].sort_values("ciclo")
        label = f"{trial.tratamento} · K{trial.kata[4]} · {trial.participante}"
        ax.plot(current.tempo_segundos / 60, current.taxa_sucesso,
                marker="o", linestyle="-" if len(current) > 1 else "None",
                color=COLORS[trial.tratamento],
                alpha=0.55 if trial.tratamento == "Manual" else 1,
                label=label)
    ax.set(xlabel="Tempo decorrido no trial (min)", ylabel="Testes passando (%)",
           ylim=(-5, 110), title="Inovação — evolução observada por ciclo")
    ax.grid(alpha=0.25)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "inovacao_evolucao_testes.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8, 5))
    for x, treatment in enumerate(("IA", "Manual")):
        group = evolution.loc[evolution.tratamento == treatment].sort_values("kata")
        for i, (_, row) in enumerate(group.iterrows()):
            xpos = x + (i - (len(group) - 1) / 2) * 0.18
            reached = row.ciclo_ate_green != ""
            ax.scatter(xpos, row.ciclo_ate_green if reached else row.n_ciclos,
                       marker="o" if reached else "x", color=COLORS[treatment], s=75)
            ax.annotate(f"K{row.kata[4]}",
                        (xpos, row.ciclo_ate_green if reached else row.n_ciclos),
                        xytext=(5, 4), textcoords="offset points", fontsize=8)
    ax.set(xlim=(-0.5, 1.5), xticks=[0, 1], xticklabels=["IA", "Manual"],
           ylabel="Ciclo em que atingiu green", title="Inovação — ciclos até green")
    ax.set_yticks(range(1, int(evolution.n_ciclos.max()) + 2))
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIGURES_DIR / "inovacao_ciclos_ate_green.png")
    plt.close(fig)


def main() -> None:
    audit, trials, cycles = load_and_audit()
    tables = analyze(audit, trials, cycles)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    for name, frame in tables.items():
        frame.to_csv(RESULTS_DIR / f"{name}.csv", index=False, encoding="utf-8")
    make_figures(trials, cycles, tables)
    print(f"Registros: {len(audit)}; incluídos: {len(trials)}; participantes: {trials.participante.nunique()}")
    print(tables["rq1_resumo"].to_string(index=False))
    print(tables["rq1_wilcoxon"].to_string(index=False))
    print(tables["rq2_resumo"].to_string(index=False))
    print(f"Tabelas: {RESULTS_DIR}; gráficos: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
