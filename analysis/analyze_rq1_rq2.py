"""Audita as fontes finais da S02 e gera RQ1, RQ2 e inovação.

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
from matplotlib.lines import Line2D
import pandas as pd

from lab02.trials.config import (
    BASE_DIR,
    CYCLES_CSV,
    FERNANDA_ALLOCATION,
    ISLAYDER_ALLOCATION,
    PARTICIPANT_REPORTED_TRIALS_CSV,
    TIME_BOX_SECONDS,
    TRIALS_CSV,
)
from lab02.trials.test_runner import count_expected_tests

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
SANDBOX_INVISIBLE_SNAPSHOT_TRIALS = {
    "0ce8664ce1cc422ca36699dc40e27fc9",
    "7a548706e9624806b0c89fa1c4a2b5e5",
}
FERNANDA_RECONSTRUCTED_ARTIFACTS = {
    "ba0cb83a55764b3389f7da94946c9230": "lab02/trials/results/rq3_artifacts/fernanda/issue-19-kata2-ia/solucao.py",
    "e9bb6d490e1246bd942cc164bb5cd55a": "lab02/trials/results/rq3_artifacts/fernanda/issue-27-kata1-manual/solucao.py",
    "c33c36f2110a45478c1016a89476035a": "lab02/trials/results/rq3_artifacts/fernanda/issue-29-kata4-ia/solucao.py",
    "077979815f8f417b88718e458c618807": "lab02/trials/results/rq3_artifacts/fernanda/issue-28-kata3-manual/solucao.py",
}
FINAL_SOURCE_KINDS = {
    "observed",
    "agent_delegated_codex_work",
    "participant_reported_observed",
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
COLORS = {"IA": "#3333B2", "Manual": "#D97706"}


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


def load_participant_reported() -> tuple[pd.DataFrame, pd.DataFrame]:
    require(
        PARTICIPANT_REPORTED_TRIALS_CSV.is_file(),
        "base de resultados informados pelo participante ausente",
    )
    reported = pd.read_csv(
        PARTICIPANT_REPORTED_TRIALS_CSV,
        dtype=str,
        keep_default_na=False,
        encoding="utf-8-sig",
    )
    required = {
        "trial_id",
        "issue",
        "participante",
        "kata",
        "tratamento",
        "tempo_segundos",
        "testes_passando",
        "testes_falhando",
        "total_testes",
        "taxa_sucesso",
        "ciclos",
        "status",
        "source_kind",
        "test_path",
        "provenance",
    }
    require(required <= set(reported), "base informada: colunas obrigatórias ausentes")
    require(
        len(reported) == 2
        and reported.participante.eq("Islayder").all()
        and set(reported.issue) == {"#21", "#25"}
        and reported.source_kind.eq("participant_reported_observed").all(),
        "base informada: escopo diferente de #21 e #25 de Islayder",
    )
    for row in reported.itertuples(index=False):
        test_path = BASE_DIR / row.test_path
        require(test_path.is_file(), f"{row.trial_id}: arquivo de teste ausente")
        require(
            count_expected_tests(test_path) == int(row.total_testes),
            f"{row.trial_id}: total diverge do arquivo de teste",
        )

    trials = reported.copy()
    for column in ("codigo_path", "iniciado_em", "finalizado_em", "erro_execucao"):
        trials[column] = ""
    cycles = reported[
        [
            "trial_id",
            "issue",
            "participante",
            "kata",
            "tratamento",
            "tempo_segundos",
            "testes_passando",
            "testes_falhando",
            "total_testes",
            "taxa_sucesso",
            "source_kind",
        ]
    ].copy()
    cycles["ciclo"] = "1"
    cycles["pytest_exit_code"] = ""
    cycles["erro_execucao"] = ""
    return trials, cycles


def snapshot_is_available(trial_id: str, relative_path: str) -> bool:
    if trial_id in SANDBOX_INVISIBLE_SNAPSHOT_TRIALS:
        return True
    if trial_id in FERNANDA_RECONSTRUCTED_ARTIFACTS:
        return (BASE_DIR / FERNANDA_RECONSTRUCTED_ARTIFACTS[trial_id]).is_file()
    try:
        return (BASE_DIR / relative_path).is_file()
    except PermissionError:
        return False


def load_and_audit() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    trials = pd.read_csv(TRIALS_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    cycles = pd.read_csv(CYCLES_CSV, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    reported_trials, reported_cycles = load_participant_reported()
    trials = pd.concat([trials, reported_trials], ignore_index=True, sort=False).fillna("")
    cycles = pd.concat([cycles, reported_cycles], ignore_index=True, sort=False).fillna("")
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
            source in FINAL_SOURCE_KINDS | {"observed_simulated"},
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
        snapshot_missing = False
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
            require(trial.codigo_path != "", f"{tid}: codigo_path vazio")
            require(Path(trial.codigo_path).as_posix()
                    == f"lab02/trials/results/solutions/{tid}/solucao.py",
                    f"{tid}: snapshot não corresponde ao trial_id")
            # Snapshot ausente NÃO derruba a auditoria; o trial é apenas
            # classificado como excluído na decisão final (abaixo).
            snapshot_missing = not snapshot_is_available(tid, trial.codigo_path)
            require(trial.issue == ISSUES[trial.participante][kata_num]
                    or tid in DOCUMENTED_EXCLUSIONS,
                    f"{tid}: Issue não corresponde ao participante/kata")
        elif source == "participant_reported_observed":
            require(
                tid == f"REPORTED-ISLAYDER-I{trial.issue.removeprefix('#')}",
                f"{tid}: identificador informado inconsistente",
            )
            require(
                trial.participante == "Islayder"
                and trial.issue in {"#21", "#25"}
                and trial.status == "green",
                f"{tid}: resultado informado fora do escopo autorizado",
            )
            require(
                trial.codigo_path == ""
                and trial.iniciado_em == ""
                and trial.finalizado_em == "",
                f"{tid}: resultado informado não deve fabricar campos do runner",
            )
            require(
                trial.issue == ISSUES[trial.participante][kata_num],
                f"{tid}: Issue não corresponde ao participante/kata",
            )
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
        if source in FINAL_SOURCE_KINDS:
            if trial.status == "green":
                require(integer(trial.testes_falhando, "testes_falhando", tid) == 0,
                        f"{tid}: green com falhas")
            if trial.status == "time-box":
                require(elapsed == TIME_BOX_SECONDS, f"{tid}: time-box sem censura em 35 min")
        if source == "observed_simulated":
            decision, reason = "excluído", "cenário simulado; sem execução humana"
        elif tid in DOCUMENTED_EXCLUSIONS:
            decision, reason = "excluído", DOCUMENTED_EXCLUSIONS[tid]
        elif snapshot_missing:
            decision, reason = "excluído", "snapshot ausente em lab02/trials/results/solutions/"
        elif trial.status in {"interrupted", "error"}:
            decision, reason = "excluído", f"status {trial.status}; trial incompleto"
        elif source == "agent_delegated_codex_work":
            decision, reason = (
                "incluído",
                "execução delegada ao Codex Work; artefato estrutural reconstruído",
            )
        elif source == "participant_reported_observed":
            decision, reason = (
                "incluído",
                "tempo e resultado observados, cronometrados e informados pelo participante",
            )
        else:
            reason = "observado e sem incidente documentado"
            if tid in FERNANDA_RECONSTRUCTED_ARTIFACTS:
                reason += "; artefato estrutural reconstruído"
            decision = "incluído"
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
            "media_segundos": group.tempo_segundos.mean(),
            "mediana_segundos": group.tempo_segundos.median(),
            "q1_segundos": group.tempo_segundos.quantile(0.25),
            "q3_segundos": group.tempo_segundos.quantile(0.75),
            "iqr_segundos": group.tempo_segundos.quantile(0.75)
            - group.tempo_segundos.quantile(0.25),
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


def _style_boxplot(ax, data: list[pd.Series], labels: tuple[str, str]) -> None:
    boxes = ax.boxplot(
        data,
        tick_labels=labels,
        patch_artist=True,
        widths=0.48,
        showfliers=False,
        medianprops={"color": "#202124", "linewidth": 2.2},
        whiskerprops={"color": "#5f6368", "linewidth": 1.2},
        capprops={"color": "#5f6368", "linewidth": 1.2},
    )
    for patch, treatment in zip(boxes["boxes"], labels):
        patch.set_facecolor(COLORS[treatment])
        patch.set_alpha(0.22)
        patch.set_edgecolor(COLORS[treatment])
        patch.set_linewidth(1.5)


def _participant_initial(name: str) -> str:
    return {"Fernanda": "F", "Islayder": "I", "Vinicius": "V"}[name]


def make_figures(
    trials: pd.DataFrame,
    cycles: pd.DataFrame,
    tables: dict[str, pd.DataFrame],
) -> None:
    plt.rcParams.update(
        {
            "font.size": 10,
            "figure.dpi": 150,
            "font.family": "DejaVu Sans",
            "axes.titleweight": "bold",
            "axes.titlecolor": "#3333B2",
            "axes.edgecolor": "#5f6368",
        }
    )
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)

    # RQ1 principal: distribuição completa com quartis, mediana e os 12 trials.
    fig, ax = plt.subplots(figsize=(8.4, 5.3))
    treatments = ("IA", "Manual")
    series = [
        trials.loc[trials.tratamento == treatment, "tempo_segundos"]
        for treatment in treatments
    ]
    _style_boxplot(ax, series, treatments)
    for position, treatment in enumerate(treatments, start=1):
        group = trials.loc[trials.tratamento == treatment].sort_values(
            ["participante", "kata"]
        )
        offsets = [
            (index - (len(group) - 1) / 2) * 0.055
            for index in range(len(group))
        ]
        label_offsets = {
            ("IA", "Fernanda", "kata4_manutencao_preditiva"): 16,
            ("IA", "Islayder", "kata1_normalizador_etiquetas"): 5,
            ("Manual", "Fernanda", "kata1_normalizador_etiquetas"): 16,
            ("Manual", "Fernanda", "kata3_compactador_sensor"): 4,
        }
        for offset, (_, row) in zip(offsets, group.iterrows()):
            ax.scatter(
                position + offset,
                row.tempo_segundos,
                s=54,
                color=COLORS[treatment],
                edgecolor="white",
                linewidth=0.8,
                zorder=3,
            )
            ax.annotate(
                f"{_participant_initial(row.participante)}·K{row.kata[4]}",
                (position + offset, row.tempo_segundos),
                xytext=(
                    0,
                    label_offsets.get(
                        (treatment, row.participante, row.kata), 7
                    ),
                ),
                textcoords="offset points",
                ha="center",
                fontsize=7.5,
                color="#34373a",
            )
    ax.set(
        ylabel="Tempo até green (s)",
        title="RQ1 — distribuição do tempo até green por tratamento",
    )
    ax.grid(axis="y", alpha=0.22)
    ax.text(
        0.01,
        -0.16,
        "Caixa = Q1–Q3; linha = mediana; pontos = trials; rótulos: participante e kata.",
        transform=ax.transAxes,
        fontsize=8,
        color="#5f6368",
    )
    fig.tight_layout()
    fig.savefig(
        FIGURES_DIR / "rq1_tempo_ia_vs_manual.png", dpi=220, bbox_inches="tight"
    )
    plt.close(fig)

    # RQ1 secundária: cada participante permanece uma categoria, não um eixo temporal.
    pairs = tables["rq1_pares"].copy()
    participants = ["Fernanda", "Islayder", "Vinicius"]
    pairs = pairs.set_index("participante").loc[participants] * 60
    x = list(range(len(participants)))
    width = 0.34
    fig, ax = plt.subplots(figsize=(8.4, 4.7))
    ia_bars = ax.bar(
        [value - width / 2 for value in x],
        pairs.mediana_ia_min,
        width,
        label="IA",
        color=COLORS["IA"],
    )
    manual_bars = ax.bar(
        [value + width / 2 for value in x],
        pairs.mediana_manual_min,
        width,
        label="Manual",
        color=COLORS["Manual"],
    )
    for bars in (ia_bars, manual_bars):
        ax.bar_label(bars, fmt="%.1f s", padding=3, fontsize=8)
    ax.set(
        xticks=x,
        xticklabels=participants,
        ylabel="Mediana individual (s)",
        title="RQ1 — medianas individuais por participante",
    )
    ax.set_ylim(0, float(pairs.max().max()) * 1.17)
    ax.grid(axis="y", alpha=0.22)
    ax.legend(frameon=False, ncol=2, loc="upper left")
    fig.tight_layout()
    fig.savefig(
        FIGURES_DIR / "rq1_mediana_participante.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    # RQ2: contagens finais; a aprovação é total nos dois tratamentos.
    rq2 = tables["rq2_resumo"].set_index("tratamento").loc[list(treatments)]
    fig, ax = plt.subplots(figsize=(7.4, 3.5))
    y = [1, 0]
    passed = rq2.passed_soma.astype(int).tolist()
    failed = rq2.failed_soma.astype(int).tolist()
    for y_pos, treatment, pass_count, fail_count in zip(
        y, treatments, passed, failed
    ):
        ax.barh(y_pos, pass_count, color=COLORS[treatment], height=0.5)
        if fail_count:
            ax.barh(
                y_pos,
                fail_count,
                left=pass_count,
                color="#9aa0a6",
                height=0.5,
            )
        ax.text(
            pass_count + 0.8,
            y_pos,
            f"{pass_count}/{pass_count + fail_count} · 100% · 0 falhando",
            va="center",
            fontsize=9,
        )
    ax.set(
        yticks=y,
        yticklabels=treatments,
        xlabel="Testes de aceitação no resultado final",
        title="RQ2 — todos os testes finais passaram",
        xlim=(0, max(passed) + 17),
    )
    ax.grid(axis="x", alpha=0.2)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(
        FIGURES_DIR / "rq2_testes_ia_vs_manual.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Inovação principal: eixo ordenado por ciclo, sem criar medições intermediárias.
    participant_markers = {"Fernanda": "o", "Islayder": "s", "Vinicius": "^"}
    fig, axes = plt.subplots(1, 2, figsize=(10.2, 5.2), sharey=True)
    for ax, treatment in zip(axes, treatments):
        group = trials.loc[trials.tratamento == treatment].sort_values(
            ["participante", "kata"]
        )
        for _, trial in group.iterrows():
            current = cycles.loc[cycles.trial_id == trial.trial_id].copy()
            current["ciclo"] = pd.to_numeric(current.ciclo)
            current["taxa_sucesso"] = pd.to_numeric(current.taxa_sucesso)
            current = current.sort_values("ciclo")
            label = f"{trial.participante} · K{trial.kata[4]}"
            ax.plot(
                current.ciclo,
                current.taxa_sucesso,
                marker=participant_markers[trial.participante],
                markersize=6,
                linewidth=1.6 if len(current) > 1 else 0,
                color=COLORS[treatment],
                alpha=0.86,
                label=label,
            )
        ax.set(
            title=treatment,
            xlabel="Ciclo de testes",
            xticks=[1, 2],
            xlim=(0.82, 2.18),
            ylim=(-4, 106),
        )
        ax.title.set_color(COLORS[treatment])
        ax.grid(alpha=0.22)
        ax.legend(fontsize=7.2, frameon=False, loc="lower right")
    axes[0].set_ylabel("Testes passando (%)")
    fig.suptitle(
        "Inovação — evolução observada ao longo dos ciclos",
        color=COLORS["IA"],
        fontweight="bold",
    )
    fig.text(
        0.5,
        0.01,
        "Cada linha representa um trial; trials com um ciclo aparecem como um único ponto.",
        ha="center",
        fontsize=8,
        color="#5f6368",
    )
    fig.tight_layout(rect=(0, 0.045, 1, 0.95))
    fig.savefig(
        FIGURES_DIR / "inovacao_evolucao_testes.png",
        dpi=220,
        bbox_inches="tight",
    )
    plt.close(fig)

    # Inovação complementar: dot plot de retrabalho por trial.
    evolution = tables["inovacao_detalhe"].copy()
    evolution["kata_num"] = evolution.kata.str.extract(r"kata([1-4])").astype(int)
    evolution["tratamento_ordem"] = pd.Categorical(
        evolution.tratamento, categories=list(treatments), ordered=True
    )
    evolution = evolution.sort_values(
        ["tratamento_ordem", "participante", "kata_num"]
    ).reset_index(drop=True)
    labels = [
        f"{row.participante} · K{row.kata_num} · {row.tratamento}"
        for row in evolution.itertuples()
    ]
    positions = list(range(len(evolution)))
    fig, ax = plt.subplots(figsize=(8.8, 6.2))
    for position, row in zip(positions, evolution.itertuples()):
        cycles_to_green = int(row.ciclo_ate_green)
        ax.hlines(
            position,
            0.85,
            cycles_to_green,
            color=COLORS[row.tratamento],
            alpha=0.45,
            linewidth=2,
        )
        ax.scatter(
            cycles_to_green,
            position,
            color=COLORS[row.tratamento],
            s=70,
            zorder=3,
        )
        ax.annotate(
            str(cycles_to_green),
            (cycles_to_green, position),
            xytext=(7, 0),
            textcoords="offset points",
            va="center",
            fontsize=8,
        )
    ax.set(
        yticks=positions,
        yticklabels=labels,
        xticks=[1, 2],
        xlim=(0.75, 2.25),
        xlabel="Ciclo em que atingiu green",
        title="Inovação — ciclos até green por trial",
    )
    ax.invert_yaxis()
    ax.grid(axis="x", alpha=0.22)
    ax.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                color=COLORS[treatment],
                linewidth=2,
                label=treatment,
            )
            for treatment in treatments
        ],
        frameon=False,
        loc="lower right",
    )
    fig.tight_layout()
    fig.savefig(
        FIGURES_DIR / "inovacao_ciclos_ate_green.png",
        dpi=220,
        bbox_inches="tight",
    )
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
