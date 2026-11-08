"""Dashboard Lab04 (P4: Z para proporção × binomial exato) — entrega final (7 seções, G1–G4).

Executar a partir da raiz do repositório:  streamlit run lab04/app.py

Cada seção é uma função ``section_*(ctx)`` registrada em SECTIONS. G3/G4 leem as tabelas
agregadas de ``lab04/results`` (ou de $LAB04_RESULTS_DIR); sem hardcode de valores.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # permite `streamlit run lab04/app.py` da raiz
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from lab04.src import delivery_config as cfg
from lab04.src.captions import g1_caption, g2_caption, g3_caption, g4_caption
from lab04.src.data_adapter import get_real_dataset
from lab04.src.plots import plot_g1, plot_g2, plot_g3, plot_g4
from lab04.src.conclusion import limitations, power_findings, type1_findings
from lab04.src.formatting import num, pct, thousands
from lab04.src.real_data import summarize_ci_runs
from lab04.src.real_results import calculate_real_results, interpret_real_results
from lab04.src.real_summary import effect_summary, effect_text
from lab04.src.s02_results import combine_conditions, load_s02_tables, power_table, results_dir, type1_table
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests

# ---------------------------------------------------------------- contexto
def load_s02_context() -> dict:
    """Tabelas de Q1/Q2/Q3 (se existirem). Nunca levanta: erros viram mensagem no dashboard."""
    try:
        tables = load_s02_tables()
        available = [t for t in (tables["q1_q2"], tables["q3"]) if t is not None]
        cond = combine_conditions(available) if available else None
        return {"s02": cond, "s02_missing": [k for k, v in tables.items() if v is None], "s02_error": None}
    except (ValueError, OSError) as exc:
        return {"s02": None, "s02_missing": [], "s02_error": str(exc)}


def build_context(n: int, true_p: float, seed: int, p0: float, alpha: float) -> dict:
    real_df, source = get_real_dataset()
    real = real_df["failed"].to_numpy(dtype="int8")
    simulated = simulate_runs(n=n, p=true_p, seed=seed)
    return {
        "n": n, "true_p": true_p, "seed": seed, "p0": p0, "alpha": alpha,
        "real_df": real_df, "real": real, "source": source,
        "simulated": simulated,
        **load_s02_context(),
        "sim_results": evaluate_tests(simulated, p0=p0, alpha=alpha),
        "real_results": evaluate_tests(real, p0=p0, alpha=alpha),
    }


# ---------------------------------------------------------------- seções
def section_cenario(ctx: dict) -> None:
    st.header("1. Cenário")
    st.markdown(
        f"**Pergunta:** a probabilidade de falha de uma execução de CI (GitHub Actions) "
        f"ultrapassa a meta de {pct(ctx['p0'], 0)}?\n\n"
        f"- **H0:** p ≤ {num(ctx['p0'])} (a taxa de falha respeita a meta)\n"
        f"- **H1:** p > {num(ctx['p0'])} (a taxa de falha excede a meta) — teste **unilateral à direita**\n"
        f"- **Testes comparados:** Z para proporção × binomial exato, com α = {num(ctx['alpha'])}\n"
        f"- **Codificação:** 0 = sucesso, 1 = falha"
    )
    df = ctx["real_df"]
    summ = summarize_ci_runs(df)
    first = df.iloc[0]
    st.markdown(
        f"**Dados reais:** {summ['n']} execuções de CI concluídas (success/failure) de "
        f"`{first['repository']}`, workflow `{first['workflow_name']}` (id {first['workflow_id']}), "
        f"branch `{first['branch']}`, de {df['created_at'].min()[:10]} a {df['created_at'].max()[:10]} (UTC); "
        f"{summ['k']} falhas (p̂ = {pct(summ['p_hat'])}). Fonte: `{ctx['source']}`."
    )
    st.caption("Execuções de CI podem ser correlacionadas e a taxa de falha pode variar no tempo; "
               "o modelo Bernoulli i.i.d. é uma simplificação.")


def simulation_params_text(ctx: dict) -> str:
    """Parâmetros das simulações e de onde vieram, lidos das tabelas de G3/G4 (nunca fixos no código)."""
    real_n, real_p = len(ctx["real"]), ctx["real"].mean()
    text = (f"**Parâmetros do exemplo (G1/G2):** n = {ctx['n']}, p real = {num(ctx['true_p'])}, "
            f"semente {ctx['seed']}, p0 = {num(ctx['p0'])}; é uma amostra ilustrativa, ajustável na barra lateral. "
            f"Os dados reais têm n = {real_n} e taxa de falha de {pct(real_p)}.")
    cond = ctx.get("s02")
    if cond is None:
        return text
    reps = int(cond["repetitions"].iloc[0])
    parts = []
    for c, g in cond.groupby("condition", observed=True, sort=False):
        n = int(g["n"].iloc[0])
        why = ("próximo do n real" if abs(n - real_n) / real_n <= 0.25 else "")
        if not bool(g["normal_ok"].iloc[0]):
            why = "n·p0 < 5: amostra pequena com evento raro, onde a aproximação normal do Z é problemática"
        parts.append(f"{c}" + (f" — {why}" if why else ""))
    pmin, pmax = cond["p_true"].min(), cond["p_true"].max()
    return text + (f"\n\n**Parâmetros de G3/G4:** {thousands(reps)} repetições por cenário, semente "
                   f"{int(cond['seed'].iloc[0])}, p real de {num(pmin, 3)} a {num(pmax, 3)} "
                   f"(efeito de 0 a {num(100 * (pmax - float(cond['p0'].iloc[0])), 1)} pp), nas condições: "
                   + "; ".join(parts) + ".")


def section_dados(ctx: dict) -> None:
    st.header("2. Os dados (G1)")
    sim, real = ctx["simulated"], ctx["real"]
    fig = plot_g1(real, sim, p0=ctx["p0"],
                  sim_label=f"Simulados (p real = {num(ctx['true_p'])}, seed = {ctx['seed']})")
    st.pyplot(fig)
    st.caption(g1_caption(len(real), int(real.sum()), len(sim), int(sim.sum()), ctx["p0"]))
    st.markdown(simulation_params_text(ctx))


def section_testes(ctx: dict) -> None:
    st.header("3. Como os testes funcionam (G2)")
    res = ctx["sim_results"]
    st.pyplot(plot_g2(res))
    st.caption(g2_caption(res))
    c1, c2 = st.columns(2)
    c1.metric("Teste Z — p-valor", num(res["z_p_value"], 4))
    c1.caption("Rejeita H0" if res["reject_z"] else "Não rejeita H0")
    c2.metric("Binomial exato — p-valor", num(res["binomial_p_value"], 4))
    c2.caption("Rejeita H0" if res["reject_binomial"] else "Não rejeita H0")
    with st.expander("Detalhes numéricos da amostra simulada"):
        st.json(res)


def _s02_unavailable(ctx: dict) -> bool:
    """Mostra aviso e devolve True quando G3/G4 não podem ser desenhados."""
    if ctx["s02_error"]:
        st.error(f"Não foi possível ler as tabelas de simulação: {ctx['s02_error']}")
        return True
    if ctx["s02"] is None:
        st.info(f"Tabelas de Q1/Q2/Q3 não encontradas em `{results_dir()}`. "
                "Gere com `python -m lab04.src.s02_experiments` (Issue #81) e o equivalente de Q3 (Issue #82).")
        return True
    if ctx["s02_missing"]:
        st.warning("Tabela(s) ausente(s): " + ", ".join(ctx["s02_missing"]) +
                   ". Os gráficos mostram apenas as condições disponíveis.")
    return False


def section_erro_tipo_i(ctx: dict) -> None:
    st.header("4. Erro tipo I (G3)")
    if _s02_unavailable(ctx):
        return
    t1 = type1_table(ctx["s02"])
    st.pyplot(plot_g3(t1))
    st.caption(g3_caption(t1))
    with st.expander("Tabela agregada usada no G3 (dados simulados)"):
        st.dataframe(t1, hide_index=True)


def section_poder(ctx: dict) -> None:
    st.header("5. Poder (G4)")
    if _s02_unavailable(ctx):
        return
    pw = power_table(ctx["s02"])
    st.pyplot(plot_g4(pw))
    st.caption(g4_caption(pw, float(pw["alpha"].iloc[0])))
    with st.expander("Tabela agregada usada no G4 (dados simulados)"):
        st.dataframe(pw, hide_index=True)


def section_dados_reais(ctx: dict) -> None:
    st.header("6. Dados reais")
    res = calculate_real_results(ctx["real_df"], p0=ctx["p0"], alpha=ctx["alpha"])
    rows = res["table_rows"]
    verdict = lambda rejected: "Rejeita H₀" if rejected else "Não rejeita H₀"  # noqa: E731
    table = pd.DataFrame({
        "Teste": [r["test"] for r in rows],
        "Estatística": [f"{r['statistic_name']} = " + (num(r["statistic"], 3) if r["statistic_name"] == "Z"
                                                       else str(int(r["statistic"]))) for r in rows],
        "p-valor (unilateral à direita)": [num(r["p_value"], 4) for r in rows],
        "Efeito p̂−p₀ (p.p.)": [f"{r['effect_pp']:.2f}" for r in rows],
        "Conclusão": [verdict(r["reject_h0"]) for r in rows],
    })
    st.dataframe(table, hide_index=True)
    st.caption(interpret_real_results(res))
    st.caption(effect_text(effect_summary(res["k"], res["n"], res["p0"])))
    st.caption(f"Hipóteses e α conforme a barra lateral (p0 = {num(res['p0'])}, α = {num(res['alpha'])}); "
               f"n = {res['n']} execuções, {res['k']} falhas.")


def section_conclusao(ctx: dict) -> None:
    st.header("7. Conclusão")
    st.markdown("#### O que o grupo esperava antes de simular")
    if cfg.EXPECTATIVA_PREVIA:
        st.markdown(cfg.EXPECTATIVA_PREVIA)
    else:
        st.markdown("⚠️ **Pendente:** o grupo precisa registrar em `lab04/src/delivery_config.py` "
                    "(EXPECTATIVA_PREVIA) qual teste esperava que se saísse melhor, e por quê, escrita antes de ver os resultados.")
    st.markdown("#### O que a simulação encontrou")
    if ctx["s02"] is None:
        st.markdown("⚠️ **Achados indisponíveis:** faltam as tabelas de simulação (seções 4 e 5).")
    else:
        t1, pw = type1_table(ctx["s02"]), power_table(ctx["s02"])
        st.markdown("**Erro tipo I (G3):**\n" + "\n".join(f"- {t}" for t in type1_findings(t1)))
        st.markdown("**Poder (G4):**\n" + "\n".join(f"- {t}" for t in power_findings(pw)))
        rr = ctx["real_results"]
        same = rr["reject_z"] == rr["reject_binomial"]
        st.markdown("**Dados reais:** " + (
            f"os dois testes {'rejeitam' if rr['reject_z'] else 'não rejeitam'} H0 (n = {rr['n']}, {rr['k']} falhas)."
            if same else "os dois testes chegaram a conclusões diferentes."))
    st.markdown("#### Recomendação")
    if cfg.RECOMENDACAO:
        st.markdown(cfg.RECOMENDACAO)
    else:
        st.markdown("⚠️ **Pendente:** o grupo precisa escrever em `lab04/src/delivery_config.py` "
                    "(RECOMENDACAO) qual teste usar no cenário e em que situação a escolha mudaria.")
    st.markdown("#### Ressalvas")
    conds = [] if ctx["s02"] is None else list(ctx["s02"]["condition"].cat.categories)
    st.markdown("\n".join(f"- {t}" for t in limitations(ctx["real_df"], len(ctx["real"]), conds)))


SECTIONS = [section_cenario, section_dados, section_testes, section_erro_tipo_i, section_poder,
            section_dados_reais, section_conclusao]


# ---------------------------------------------------------------- app
def main() -> None:
    st.set_page_config(page_title="Lab04 — Testes de hipótese (P4)", layout="wide")
    st.title("Lab04 — Testes de hipótese por dentro: Z para proporção × binomial exato")
    st.markdown(f"**Dashboard:** {cfg.DASHBOARD_URL or '(link pendente)'} · "
                f"**Repositório / GitHub Projects:** {cfg.REPO_URL or '(link pendente)'}")
    pending = cfg.pending_items()
    if pending:
        st.warning("Pendências antes da entrega final: " + "; ".join(pending) + ".")

    with st.sidebar:
        st.header("Amostra simulada de exemplo")
        n = st.number_input("n (execuções de CI)", min_value=5, max_value=1000, value=30, step=5)
        true_p = st.slider("p real da simulação", 0.0, 0.5, 0.10, 0.01)
        seed = st.number_input("Semente", min_value=0, value=42, step=1)
        st.header("Hipóteses")
        p0 = st.slider("Meta p0", 0.01, 0.20, 0.05, 0.01)
        alpha = st.select_slider("α", options=[0.01, 0.05, 0.10], value=0.05)

    ctx = build_context(int(n), float(true_p), int(seed), float(p0), float(alpha))
    for section in SECTIONS:
        section(ctx)
        st.divider()


if __name__ == "__main__":  # `streamlit run` e AppTest executam o script como __main__
    main()