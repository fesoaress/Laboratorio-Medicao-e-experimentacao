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
from lab04.src.formatting import num, p_value, pct, thousands
from lab04.src.real_results import calculate_real_results, interpret_real_results
from lab04.src.real_summary import effect_summary, effect_text
from lab04.src.robustness import null_rejection_regions
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
        "n": n, "true_p": true_p, "seed": seed,
        "real_df": real_df, "real": real, "source": source,
        "simulated": simulated,
        **load_s02_context(),
        "sim_results": evaluate_tests(simulated, p0=p0, alpha=alpha),
        "real_results": calculate_real_results(real_df, p0=cfg.P0, alpha=cfg.ALPHA),
    }


# ---------------------------------------------------------------- seções
def section_cenario(ctx: dict) -> None:
    st.header("1. Cenário", anchor="cenario")
    res = ctx["real_results"]
    st.markdown(
        "O estudo avalia a probabilidade de falha de uma execução concluída de CI.\n\n"
        f"- **H₀** · p ≤ {num(res['p0'])}\n"
        f"- **H₁** · p > {num(res['p0'])}\n"
        f"- **Teste unilateral à direita** · α = {pct(res['alpha'], 0)}"
    )
    df = ctx["real_df"]
    first = df.iloc[0]
    st.markdown(
        f"**Amostra real** · {res['n']} execuções do GitHub Actions de "
        f"`{first['repository']}`, workflow `{first['workflow_name']}` (id {first['workflow_id']}), "
        f"branch `{first['branch']}`, de {df['created_at'].min()[:10]} a {df['created_at'].max()[:10]} (UTC). "
        f"São incluídas apenas execuções com conclusão `success` (0) ou `failure` (1). "
        f"Snapshot: `{ctx['source']}`."
    )
    st.caption("Execuções de CI podem ser correlacionadas e a taxa de falha pode variar no tempo; "
               "o modelo Bernoulli i.i.d. é uma simplificação.")


def simulation_params_text(ctx: dict) -> str:
    """Parâmetros das simulações e de onde vieram, lidos das tabelas de G3/G4 (nunca fixos no código)."""
    real_n = len(ctx["real"])
    text = (f"**Amostra ilustrativa (G1/G2)** · n = {ctx['n']}, "
            f"probabilidade de falha = {pct(ctx['true_p'], 0)}, semente {ctx['seed']}.")
    cond = ctx.get("s02")
    if cond is None:
        return text
    reps = int(cond["repetitions"].iloc[0])
    parts = []
    for c, g in cond.groupby("condition", observed=True, sort=False):
        n = int(g["n"].iloc[0])
        why = ("próximo do n real" if abs(n - real_n) / real_n <= 0.25 else "")
        if not bool(g["normal_ok"].iloc[0]):
            why = "poucas falhas ou poucos sucessos esperados sob H₀, o que prejudica a aproximação Z"
        parts.append(f"{c}" + (f" — {why}" if why else ""))
    pmin, pmax = cond["p_true"].min(), cond["p_true"].max()
    return text + (f"\n\n**Experimento de G3/G4** · {thousands(reps)} repetições por cenário, "
                   f"semente {int(cond['seed'].iloc[0])}, p de {pct(pmin, 1)} a {pct(pmax, 1)}. "
                   "Condições simuladas\n\n" + "\n".join(f"- {part}" for part in parts))


def section_dados(ctx: dict) -> None:
    st.header("2. Os dados (G1)", anchor="dados")
    sim, real = ctx["simulated"], ctx["real"]
    fig = plot_g1(real, sim, p0=cfg.P0)
    st.pyplot(fig)
    st.caption(g1_caption(len(real), int(real.sum()), len(sim), int(sim.sum()), cfg.P0))
    st.markdown(simulation_params_text(ctx))


def section_testes(ctx: dict) -> None:
    st.header("3. Como os testes funcionam (G2)", anchor="testes")
    res = ctx["sim_results"]
    st.caption(f"Exploração da mesma amostra simulada do G1 · p₀ = {pct(res['p0'], 0)} e α = {pct(res['alpha'], 0)}.")
    st.pyplot(plot_g2(res))
    st.caption(g2_caption(res))
    c1, c2 = st.columns(2)
    c1.metric("Teste Z — p-valor", p_value(res["z_p_value"]))
    c1.caption("Rejeita H0" if res["reject_z"] else "Não rejeita H0")
    c2.metric("Binomial exato — p-valor", p_value(res["binomial_p_value"]))
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
                "Gere Q1/Q2 com `python -m lab04.src.s02_experiments` e Q3 com `python -m lab04.src.robustness`.")
        return True
    if ctx["s02_missing"]:
        st.warning("Tabela(s) ausente(s): " + ", ".join(ctx["s02_missing"]) +
                   ". Os gráficos mostram apenas as condições disponíveis.")
    return False


def section_erro_tipo_i(ctx: dict) -> None:
    st.header("4. Erro tipo I (G3)", anchor="erro-tipo-i")
    if _s02_unavailable(ctx):
        return
    t1 = type1_table(ctx["s02"])
    st.pyplot(plot_g3(t1))
    st.caption(g3_caption(t1))
    with st.expander("Tabela agregada usada no G3 (dados simulados)"):
        st.dataframe(t1, hide_index=True)


def section_poder(ctx: dict) -> None:
    st.header("5. Poder (G4)", anchor="poder")
    if _s02_unavailable(ctx):
        return
    pw = power_table(ctx["s02"])
    st.pyplot(plot_g4(pw))
    st.caption(g4_caption(pw, float(pw["alpha"].iloc[0])))
    with st.expander("Tabela agregada usada no G4 (dados simulados)"):
        st.dataframe(pw, hide_index=True)


def section_dados_reais(ctx: dict) -> None:
    st.header("6. Dados reais", anchor="resultados")
    res = ctx["real_results"]
    st.markdown(f"**{res['n']} execuções** · **{res['k']} falhas** · **{pct(res['p_hat'])} de falhas observadas**")
    rows = res["table_rows"]
    verdict = lambda rejected: "Rejeita H₀" if rejected else "Não rejeita H₀"  # noqa: E731
    table = pd.DataFrame({
        "Teste": [r["test"] for r in rows],
        "Estatística": [f"{r['statistic_name']} = " + (num(r["statistic"], 3) if r["statistic_name"] == "Z"
                                                       else str(int(r["statistic"]))) for r in rows],
        "p-valor (unilateral à direita)": [p_value(r["p_value"]) for r in rows],
        "Efeito p̂−p₀ (p.p.)": [num(r["effect_pp"]) for r in rows],
        "Conclusão": [verdict(r["reject_h0"]) for r in rows],
    })
    st.dataframe(table, hide_index=True)
    st.caption(interpret_real_results(res))
    st.caption(effect_text(effect_summary(res["k"], res["n"], res["p0"])))
    st.caption(f"Hipóteses e α do cenário oficial (p₀ = {num(res['p0'])}, α = {num(res['alpha'])}).")


def section_conclusao(ctx: dict) -> None:
    st.header("7. Conclusão", anchor="conclusao")
    st.markdown("#### Expectativa inicial")
    st.markdown(cfg.EXPECTATIVA_PREVIA)
    st.markdown("#### O que a simulação encontrou")
    cond = ctx["s02"]
    if cond is None:
        st.markdown("⚠️ **Achados indisponíveis:** faltam as tabelas de simulação (seções 4 e 5).")
    else:
        t1, pw = type1_table(cond), power_table(cond)
        st.markdown("**Q1 · Erro tipo I**\n\n" + "\n".join(f"- {t}" for t in type1_findings(t1)))
        st.markdown("**Q2 · Poder**\n\n" + "\n".join(f"- {t}" for t in power_findings(pw)))
        critical = cond.loc[~cond["normal_ok"], ["n", "p0", "alpha"]].drop_duplicates()
        for n, p0, alpha in critical.itertuples(index=False, name=None):
            region = null_rejection_regions(int(n), p0, alpha)
            z_size = pct(region["z_actual_null_rejection"])
            exact_size = pct(region["binomial_actual_null_rejection"])
            st.markdown(
                f"**Q3 · Aproximação normal com n = {int(n)}**. As contagens esperadas sob H₀ são "
                f"{num(n * p0, 1)} falhas e {num(n * (1 - p0), 1)} sucessos. A aproximação Z é "
                f"imprecisa quando uma delas é pequena. Pelas regiões de rejeição, as taxas teóricas "
                f"sob p = p₀ são {z_size} para o Z e {exact_size} para o binomial exato."
            )
        st.markdown(
            "A contagem de falhas só muda em saltos inteiros, o que pode deixar o binomial exato "
            "abaixo de α. Compare o poder junto com o erro tipo I. Uma regra de rejeição menos exigente "
            "pode aumentar ambos. Para um mesmo efeito, aumentar n tende a elevar o poder."
        )
    st.markdown("#### Recomendação")
    st.markdown(cfg.RECOMENDACAO)
    st.markdown("#### Ressalvas")
    conds = [] if ctx["s02"] is None else list(ctx["s02"]["condition"].cat.categories)
    st.markdown("\n".join(f"- {t}" for t in limitations(ctx["real_df"], len(ctx["real"]), conds)))


SECTIONS = [section_cenario, section_dados, section_testes, section_erro_tipo_i, section_poder,
            section_dados_reais, section_conclusao]


# ---------------------------------------------------------------- app
def main() -> None:
    st.set_page_config(page_title="Lab04 — Testes de hipótese (P4)", layout="centered")
    st.caption("PUC Minas · Medição e Experimentação de Software · Laboratório 04")
    st.title("A taxa de falhas do CI ultrapassa 5%?")
    st.markdown("P4 · Teste Z para uma proporção e teste binomial exato")
    links = [f"[Repositório]({cfg.REPO_URL}/tree/Laboratorio-4/lab04)"]
    if cfg.DASHBOARD_URL:
        links.append(f"[Dashboard publicado]({cfg.DASHBOARD_URL})")
    st.markdown(" · ".join(links))

    with st.sidebar:
        st.markdown(
            "**Neste dashboard**\n\n"
            "1. [Cenário](#cenario)\n"
            "2. [Dados e G1](#dados)\n"
            "3. [Testes e G2](#testes)\n"
            "4. [Erro tipo I e G3](#erro-tipo-i)\n"
            "5. [Poder e G4](#poder)\n"
            "6. [Resultados reais](#resultados)\n"
            "7. [Conclusão](#conclusao)"
        )
        st.divider()
        st.header("Amostra simulada")
        st.caption("Ajuste a amostra de G1 e G2.")
        n = st.number_input("n (execuções de CI)", min_value=5, max_value=1000, value=30, step=5)
        true_p = st.slider("Probabilidade de falha na simulação", 0.0, 0.5, 0.10, 0.01)
        seed = st.number_input("Semente", min_value=0, value=42, step=1)
        st.header("Hipóteses do G2")
        st.caption("Explore outra meta ou outro α no G2. O cenário oficial permanece em 5%.")
        p0 = st.slider("Meta p₀", 0.01, 0.20, cfg.P0, 0.01)
        alpha = st.select_slider("α", options=[0.01, 0.05, 0.10], value=cfg.ALPHA)

    ctx = build_context(int(n), float(true_p), int(seed), float(p0), float(alpha))
    for section in SECTIONS:
        section(ctx)
        st.divider()


if __name__ == "__main__":  # `streamlit run` e AppTest executam o script como __main__
    main()
