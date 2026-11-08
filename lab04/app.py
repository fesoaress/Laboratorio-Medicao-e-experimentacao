"""Dashboard Lab04 (P4: Z para proporção × binomial exato) — S01 (G1, G2) e S02 (G3, G4).

Executar a partir da raiz do repositório:  streamlit run lab04/app.py

Cada seção é uma função ``section_*(ctx)`` registrada em SECTIONS. G3/G4 leem as tabelas
agregadas de ``lab04/results`` (ou de $LAB04_RESULTS_DIR); sem hardcode de valores.
"""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:  # permite `streamlit run lab04/app.py` da raiz
    sys.path.insert(0, str(ROOT))

import pandas as pd
import streamlit as st

from lab04.src.captions import g1_caption, g2_caption, g3_caption, g4_caption
from lab04.src.data_adapter import get_real_dataset
from lab04.src.plots import plot_g1, plot_g2, plot_g3, plot_g4
from lab04.src.real_data import summarize_ci_runs
from lab04.src.real_results import calculate_real_results, interpret_real_results
from lab04.src.s02_results import combine_conditions, load_s02_tables, power_table, results_dir, type1_table
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests

DASHBOARD_URL = os.getenv("LAB04_DASHBOARD_URL")
PROJECTS_URL = os.getenv("LAB04_PROJECTS_URL")
REPO_URL = "https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/tree/Laboratorio-4"


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
    real_analysis = calculate_real_results(real_df, p0=p0, alpha=alpha)
    return {
        "n": n, "true_p": true_p, "seed": seed, "p0": p0, "alpha": alpha,
        "real_df": real_df, "real": real, "source": source,
        "simulated": simulated,
        **load_s02_context(),
        "sim_results": evaluate_tests(simulated, p0=p0, alpha=alpha),
        "real_results": real_analysis["tests"],
        "real_analysis": real_analysis,
    }


# ---------------------------------------------------------------- seções
def section_cenario(ctx: dict) -> None:
    st.header("1. Cenário")
    st.markdown(
        f"**Pergunta:** a probabilidade de falha de uma execução de CI (GitHub Actions) "
        f"ultrapassa a meta de {ctx['p0']:.0%}?\n\n"
        f"- **H0:** p ≤ {ctx['p0']:g} (a taxa de falha respeita a meta)\n"
        f"- **H1:** p > {ctx['p0']:g} (a taxa de falha excede a meta) — teste **unilateral à direita**\n"
        f"- **Testes comparados:** Z para proporção × binomial exato, com α = {ctx['alpha']:g}\n"
        f"- **Codificação:** 0 = sucesso, 1 = falha"
    )
    df = ctx["real_df"]
    summ = summarize_ci_runs(df)
    first = df.iloc[0]
    st.markdown(
        f"**Dados reais:** {summ['n']} execuções de CI concluídas (success/failure) de "
        f"`{first['repository']}`, workflow `{first['workflow_name']}` (id {first['workflow_id']}), "
        f"branch `{first['branch']}`, de {df['created_at'].min()[:10]} a {df['created_at'].max()[:10]} (UTC); "
        f"{summ['k']} falhas (p̂ = {summ['p_hat']:.2%}). "
        f"Fonte: [GitHub Actions — {first['workflow_name']}](https://github.com/{first['repository']}/actions/workflows/test.yml), "
        f"registrada em `{ctx['source']}`."
    )
    st.markdown(
        "A coleta usou execuções `push` concluídas do mesmo workflow e branch. "
        "Entraram no denominador somente `success` e `failure`; canceladas, "
        "ignoradas e sem conclusão foram excluídas. A regra e a consulta à API "
        "estão documentadas em `lab04/docs/cenario_s01.md`."
    )
    st.caption("Execuções de CI podem ser correlacionadas e a taxa de falha pode variar no tempo; "
               "o modelo Bernoulli i.i.d. é uma simplificação.")


def section_dados(ctx: dict) -> None:
    st.header("2. Os dados (G1)")
    sim, real = ctx["simulated"], ctx["real"]
    fig = plot_g1(real, sim, p0=ctx["p0"],
                  sim_label=f"Simulados (p real = {ctx['true_p']:g}, seed = {ctx['seed']})")
    st.pyplot(fig)
    st.caption(g1_caption(len(real), int(real.sum()), len(sim), int(sim.sum()), ctx["p0"]))
    st.markdown(
        f"**Distribuição observada:** {len(real) - int(real.sum())} sucessos e "
        f"{int(real.sum())} falhas em {len(real)} execuções "
        f"(taxa de falha {int(real.sum()) / len(real):.2%}). "
        "O painel simulado é um exemplo controlado pelos parâmetros na barra lateral; "
        "suas observações não são acrescentadas à amostra real."
    )


def section_testes(ctx: dict) -> None:
    st.header("3. Como os testes funcionam (G2)")
    res = ctx["sim_results"]
    st.pyplot(plot_g2(res))
    st.caption(g2_caption(res))
    c1, c2 = st.columns(2)
    c1.metric("Teste Z — p-valor", f"{res['z_p_value']:.4f}",
              "rejeita H0" if res["reject_z"] else "não rejeita H0", delta_color="off")
    c2.metric("Binomial exato — p-valor", f"{res['binomial_p_value']:.4f}",
              "rejeita H0" if res["reject_binomial"] else "não rejeita H0", delta_color="off")
    with st.expander("Detalhes numéricos da amostra simulada"):
        st.json(res)
    with st.expander("Os mesmos testes nos dados reais (prévia da seção 6)"):
        rr = ctx["real_results"]
        st.dataframe(pd.DataFrame([
            {"teste": "Z para proporção", "estatística": rr["z_statistic"], "p-valor": rr["z_p_value"],
             "rejeita H0": rr["reject_z"]},
            {"teste": "Binomial exato", "estatística": rr["k"], "p-valor": rr["binomial_p_value"],
             "rejeita H0": rr["reject_binomial"]},
        ]), hide_index=True)
        st.caption(f"n = {rr['n']}, falhas = {rr['k']}, p̂ = {rr['p_hat']:.3f}. "
                   "Um p-valor alto não prova que H0 é verdadeira.")


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
    result = ctx["real_analysis"]
    st.markdown(
        f"Na amostra observada, **n={result['n']}** execuções e **k={result['k']}** "
        f"falhas dão **p̂={result['p_hat']:.2%}**. A tabela aplica ambos os testes "
        f"à mesma amostra, com p₀={result['p0']:.0%} e α={result['alpha']:.0%}. "
        "O efeito é a diferença assinada **100×(p̂−p₀)**, em pontos percentuais; "
        "por isso é igual nas duas linhas."
    )
    rows = []
    for item in result["table_rows"]:
        statistic = (f"{item['statistic']:.3f}" if item["statistic_name"] == "Z"
                     else str(item["statistic"]))
        rows.append({
            "Teste": item["test"],
            "Estatística": f"{item['statistic_name']} = {statistic}",
            "p-valor": f"{item['p_value']:.4f}",
            "Efeito p̂−p₀ (p.p.)": f"{item['effect_pp']:+.2f}",
            "Conclusão": "Rejeita H₀" if item["reject_h0"] else "Não rejeita H₀",
        })
    st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
    st.caption(
        f"{interpret_real_results(result)} O teste exato usa K, a contagem de falhas; "
        "o teste Z usa a estatística padronizada. Um p-valor não mede a importância "
        "prática da diferença observada."
    )


def section_conclusao(ctx: dict) -> None:
    st.header("7. Conclusão")
    st.markdown(
        "A expectativa inicial era que a aproximação normal do Z pudesse "
        "divergir do binomial exato quando houvesse poucas falhas esperadas, "
        "enquanto uma amostra maior aproximaria as decisões."
    )
    if ctx["s02"] is not None:
        t1 = type1_table(ctx["s02"]).sort_values("n")
        if len(t1) >= 2:
            small, reference = t1.iloc[0], t1.iloc[-1]
            st.markdown(
                f"**Q1 e Q3:** em n={int(small['n'])}, o Z rejeitou "
                f"{small['z_rate']:.2%} das vezes sob H₀ e o exato "
                f"{small['binomial_rate']:.2%}; com n={int(reference['n'])}, "
                f"as taxas foram {reference['z_rate']:.2%} e "
                f"{reference['binomial_rate']:.2%}. No cenário pequeno, "
                f"o Z foi {small['z_status']} e o exato "
                f"{small['binomial_status']} em relação a "
                f"α={small['alpha']:.0%}."
            )
            pw = power_table(ctx["s02"])
            effect_five = pw[(pw["effect_pp"] - 5).abs() < 1e-8]
            small_power = effect_five[effect_five["n"] == small["n"]]
            reference_power = effect_five[effect_five["n"] == reference["n"]]
            if not small_power.empty and not reference_power.empty:
                s, r = small_power.iloc[0], reference_power.iloc[0]
                st.markdown(
                    f"**Q2:** para um aumento de 5 pontos percentuais "
                    f"(p real={s['p_true']:.0%}), o poder foi "
                    f"{s['z_rate']:.2%} no Z e {s['binomial_rate']:.2%} no exato "
                    f"em n={int(small['n'])}; em n={int(reference['n'])}, "
                    f"foram {r['z_rate']:.2%} e {r['binomial_rate']:.2%}. "
                    "O maior poder do Z "
                    "na amostra pequena vem acompanhado de mais falsos positivos."
                )
        simulated_p0 = float(ctx["s02"]["p0"].iloc[0])
        simulated_alpha = float(ctx["s02"]["alpha"].iloc[0])
        if ctx["p0"] != simulated_p0 or ctx["alpha"] != simulated_alpha:
            st.warning(
                f"G3/G4 foram gerados com p₀={simulated_p0:.0%} e "
                f"α={simulated_alpha:.0%}. Para comparar diretamente com os "
                "testes reais, use esses mesmos valores na barra lateral."
            )
    else:
        st.info("As tabelas de Q1–Q3 não estão disponíveis para resumir a simulação.")

    st.markdown(f"**Dados reais:** {interpret_real_results(ctx['real_analysis'])}")
    st.markdown(
        "**Recomendação:** para a decisão formal neste cenário de falhas raras, "
        "preferimos o teste binomial exato, que não depende da aproximação normal "
        "e controlou o erro tipo I no cenário pequeno. O Z continua útil para "
        "comparação didática; seu poder maior em n=30 não deve ser interpretado "
        "isoladamente como vantagem."
    )
    st.caption(
        "A conclusão observada se restringe a um workflow, branch e período. "
        "Execuções próximas podem compartilhar causas de falha, contrariando "
        "a independência Bernoulli usada nos testes e nas simulações; não rejeitar "
        "H₀ não prova que a taxa verdadeira esteja abaixo da meta."
    )


SECTIONS = [
    section_cenario, section_dados, section_testes, section_erro_tipo_i,
    section_poder, section_dados_reais, section_conclusao,
]


# ---------------------------------------------------------------- app
def main() -> None:
    st.set_page_config(page_title="Lab04 — Testes de hipótese (P4)", layout="wide")
    st.title("Lab04 — Testes de hipótese por dentro: Z para proporção × binomial exato")
    links = [f"[Código e dados (Laboratorio-4)]({REPO_URL})"]
    if DASHBOARD_URL:
        links.append(f"[Dashboard publicado]({DASHBOARD_URL})")
    if PROJECTS_URL:
        links.append(f"[GitHub Projects]({PROJECTS_URL})")
    st.markdown(" · ".join(links))

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


if __name__ == "__main__":
    main()
