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
from lab04.src.plots import critical_k, critical_k_z, plot_g1, plot_g2, plot_g3, plot_g4
from lab04.src.conclusion import limitations, power_sentence
from lab04.src.formatting import num, p_value, pct, pp, thousands
from lab04.src.real_results import calculate_real_results, interpret_real_results
from lab04.src.real_summary import effect_summary, effect_text
from lab04.src.s02_results import combine_conditions, load_s02_tables, power_table, results_dir, type1_table
from lab04.src.simulation import simulate_runs
from lab04.src.stat_tests import evaluate_tests


G1_REFERENCE_N = 200  # Valor inicial ajustável; Q1/Q2 usam as tabelas oficiais.


def decision_text(rejected: bool) -> str:
    return "Rejeita H₀" if rejected else "Não rejeita H₀"


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


def build_context(n: int, true_p: float, seed: int, p0: float, alpha: float,
                  reference_n: int = G1_REFERENCE_N) -> dict:
    real_df, source = get_real_dataset()
    real = real_df["failed"].to_numpy(dtype="int8")
    simulated = simulate_runs(n=n, p=true_p, seed=seed)
    # Outra semente evita que o painel de referência repita o prefixo da amostra pequena.
    simulated_reference = simulate_runs(n=reference_n, p=true_p, seed=seed + 1)
    return {
        "n": n, "reference_n": reference_n, "true_p": true_p, "seed": seed,
        "real_df": real_df, "real": real, "source": source,
        "simulated": simulated,
        "simulated_reference": simulated_reference,
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


def simulation_params_text(ctx: dict) -> str:
    """Parâmetros das simulações e de onde vieram, lidos das tabelas de G3/G4 (nunca fixos no código)."""
    real_n = len(ctx["real"])
    text = (
        f"**G1 · exemplos ilustrativos** · uma amostra ajustável com n = {ctx['n']} e outra "
        f"de referência com n = {len(ctx['simulated_reference'])} (o padrão é n = 200, próximo das {real_n} reais). "
        f"Ambas usam probabilidade hipotética de falha de {pct(ctx['true_p'], 0)} "
        f"e sementes distintas {ctx['seed']} e {ctx['seed'] + 1}; "
        "não representam as 10.000 repetições oficiais. "
        f"**G2** utiliza somente a amostra ajustável de n = {ctx['n']}. "
        "A taxa observada nos dados reais é apresentada separadamente."
    )
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
    st.markdown(
        "**Variável Bernoulli:** cada execução concluída gera um resultado binário "
        "(0 = sucesso; 1 = falha). Os dados reais vêm do GitHub Actions; "
        "os outros dois painéis são amostras simuladas ilustrativas."
    )
    sim, reference, real = ctx["simulated"], ctx["simulated_reference"], ctx["real"]
    fig = plot_g1(real, sim, reference, p0=cfg.P0)
    st.pyplot(fig)
    st.caption(g1_caption(
        len(real), int(real.sum()), len(sim), int(sim.sum()),
        len(reference), int(reference.sum()), ctx["true_p"], cfg.P0,
    ))
    st.markdown(
        f"**Por que comparar os tamanhos?** Uma única falha representa "
        f"**{num(100 / len(sim), 2)} p.p.** em n = {len(sim)} e "
        f"**{num(100 / len(reference), 2)} p.p.** em n = {len(reference)}. "
        "Em geral, quanto menor n, maior a variabilidade relativa; G3/G4 verificam "
        "o comportamento dos testes em 10.000 repetições por cenário. "
        "Nos experimentos oficiais, n = 200 foi escolhido por ser próximo das "
        "169 execuções reais; n = 30 representa o caso de amostra pequena."
    )
    with st.expander("Parâmetros e justificativa das simulações", expanded=False):
        st.markdown(simulation_params_text(ctx))


def section_testes(ctx: dict) -> None:
    st.header("3. Como os testes funcionam (G2)", anchor="testes")
    res = ctx["sim_results"]
    st.caption(
        f"Mesma amostra ajustável do G1 (n = {res['n']}, K = {res['k']} falhas); "
        f"a outra amostra ilustrativa, n = {ctx['reference_n']}, não entra neste teste. "
        f"p₀ = {pct(res['p0'], 0)} e α = {pct(res['alpha'], 0)}."
    )
    z_k = critical_k_z(res["n"], res["p0"], res["alpha"])
    exact_k = critical_k(res["n"], res["p0"], res["alpha"])
    z_region = f"K ≥ {z_k}" if z_k is not None else "sem região de rejeição"
    exact_region = f"K ≥ {exact_k}" if exact_k is not None else "sem região de rejeição"
    st.markdown(
        f"**Comparação direta dos limiares (número de falhas):** "
        f"teste Z **{z_region}** · binomial exato **{exact_region}**. "
        "No gráfico superior estão as probabilidades binomiais discretas; "
        "no inferior, a aproximação pela curva normal."
    )
    st.pyplot(plot_g2(res))
    st.caption(g2_caption(res))
    z, exact = st.columns(2)
    z.metric("Teste Z · p-valor", p_value(res["z_p_value"]))
    z.markdown(f"**Observado** · Z = {num(res['z_statistic'], 3)}  \n"
               f"**Rejeição** · Z > {num(res['z_critical'], 3)} ({z_region})  \n"
               f"**Decisão** · {decision_text(res['reject_z'])}")
    exact.metric("Binomial exato · p-valor", p_value(res["binomial_p_value"]))
    exact.markdown(f"**Observado** · K = {res['k']} falhas  \n"
                   f"**Rejeição** · {exact_region}  \n"
                   f"**Decisão** · {decision_text(res['reject_binomial'])}")
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
    st.caption("Q1 · Simulação oficial sob H₀")
    st.pyplot(plot_g3(t1))
    st.caption(g3_caption(t1))
    st.markdown(
        "**Como interpretar:** erro tipo I é um falso alarme: concluir que a taxa de falhas "
        "ultrapassou a meta quando, na realidade, não ultrapassou. "
        "Erro tipo II é deixar de detectar uma taxa verdadeiramente acima da meta. "
        "A gravidade depende do custo de investigar falsos alarmes versus deixar falhas passar."
    )
    for row in t1.itertuples(index=False):
        st.markdown(
            f"**n = {row.n}** · Z: **{pct(row.z_rate)} ({row.z_status})**; "
            f"binomial exato: **{pct(row.binomial_rate)} ({row.binomial_status})** "
            f"· α = {pct(row.alpha, 0)}."
        )
    with st.expander("Tabela agregada usada no G3 (dados simulados)"):
        st.dataframe(t1, hide_index=True)


def section_poder(ctx: dict) -> None:
    st.header("5. Poder (G4)", anchor="poder")
    if _s02_unavailable(ctx):
        return
    pw = power_table(ctx["s02"])
    st.caption("Q2 e Q3 · Simulação oficial por tamanho do efeito")
    st.pyplot(plot_g4(pw))
    st.caption(g4_caption(pw))
    st.caption(
        "Se α fosse reduzido de 5% para 1%, a região de rejeição encolheria "
        "(ou permaneceria igual), reduzindo ou mantendo erro tipo I e poder. "
        "Isso não foi recalculado em G3/G4; ajuste α no G2 apenas para explorar o limiar."
    )
    st.markdown(
        "**Como interpretar:** poder é a probabilidade de detectar a taxa de falhas "
        "acima da meta quando ela realmente está acima. "
        "Poder maior precisa ser avaliado junto aos falsos alarmes de G3."
    )
    small_n = int(pw["n"].min())
    example = pw[(pw["n"] == small_n) & ((pw["p_true"] - 0.10).abs() < 1e-9)]
    if not example.empty:
        r = example.iloc[0]
        st.markdown(
            f"**Exemplo do gráfico (n = {small_n}, p verdadeiro = {pct(r['p_true'], 0)}; "
            f"efeito = +{num(r['effect_pp'], 1)} p.p.):** "
            f"poder do Z **{pct(r['z_rate'])}** × binomial exato **{pct(r['binomial_rate'])}**."
        )
    for condition, group in pw.groupby("condition", sort=False):
        if len(group) > 1 and ((group["z_rate"] - group["binomial_rate"]).abs() < 1e-12).all():
            st.markdown(
                f"**{condition}:** curvas dos dois testes coincidem em todos os efeitos estudados."
            )
    with st.expander("Tabela agregada usada no G4 (dados simulados)"):
        st.dataframe(pw, hide_index=True)


def section_dados_reais(ctx: dict) -> None:
    st.header("6. Dados reais", anchor="resultados")
    res = ctx["real_results"]
    observed_col, target_col, effect_col = st.columns(3)
    observed_col.metric("Falhas observadas", pct(res["p_hat"]))
    target_col.metric("Meta de falhas", pct(res["p0"], 0))
    effect_col.metric("Diferença observada", f"{num(res['effect_pp'], 2)} p.p.")
    st.markdown(
        f"**{res['k']} falhas em {res['n']} execuções**. A diferença em pontos percentuais "
        "mede o tamanho e a direção do efeito, enquanto os p-valores sustentam "
        "a decisão estatística. Não rejeitar H₀ não comprova que a meta foi atendida."
    )
    rows = res["table_rows"]
    table = pd.DataFrame({
        "Teste": [r["test"] for r in rows],
        "Estatística": [f"{r['statistic_name']} = " + (num(r["statistic"], 3) if r["statistic_name"] == "Z"
                                                       else str(int(r["statistic"]))) for r in rows],
        "p-valor": [p_value(r["p_value"]) for r in rows],
        "Efeito p̂−p₀ (p.p.)": [num(r["effect_pp"]) for r in rows],
        "Conclusão": [decision_text(r["reject_h0"]) for r in rows],
    })
    st.dataframe(table, hide_index=True)
    st.caption("Em telas estreitas, deslize a tabela para ver as demais colunas.")
    st.caption(effect_text(effect_summary(res["k"], res["n"], res["p0"])))
    st.caption(f"Hipóteses e α do cenário oficial (p₀ = {num(res['p0'])}, α = {num(res['alpha'])}). "
               "Os p-valores são unilaterais à direita e o efeito é a diferença em pontos percentuais.")


def section_conclusao(ctx: dict) -> None:
    st.header("7. Conclusão", anchor="conclusao")
    real = ctx["real_results"]
    st.markdown(
        f"Das {real['n']} execuções observadas, {real['k']} falharam ({pct(real['p_hat'])}). "
        + interpret_real_results(real)
    )
    st.markdown("### Expectativa inicial")
    st.markdown(cfg.EXPECTATIVA_PREVIA)
    st.markdown("### O que a simulação encontrou")
    cond = ctx["s02"]
    if cond is None:
        st.markdown("⚠️ **Achados indisponíveis:** faltam as tabelas de simulação (seções 4 e 5).")
    else:
        type1 = type1_table(cond)
        for row in type1.loc[type1["normal_ok"]].itertuples(index=False):
            gap = max(abs(row.z_rate - row.alpha), abs(row.binomial_rate - row.alpha))
            st.markdown(
                f"**Q1 · Erro tipo I (n = {row.n})** · Z {pct(row.z_rate)} e binomial exato "
                f"{pct(row.binomial_rate)}. A maior distância ao nível nominal de {pct(row.alpha, 0)} "
                f"foi de {pp(100 * gap, 2)}."
            )

        power = []
        for _, group in power_table(cond).sort_values("effect_pp").groupby("condition", sort=False):
            positive = group[group["effect_pp"] > 0]
            comparison = power_sentence(group)
            if not positive.empty:
                if group["z_rate"].equals(group["binomial_rate"]):
                    comparison = "as curvas coincidiram em todos os efeitos estudados"
                else:
                    example = positive.iloc[0]
                    comparison += (f". A {pp(example['effect_pp'])} de efeito, o poder foi de "
                                   f"{pct(example['z_rate'])} no Z e {pct(example['binomial_rate'])} "
                                   "no binomial exato")
            power.append(f"Em n = {int(group['n'].iloc[0])}, {comparison}.")
        st.markdown(
            "**Q2 · Poder** · " + " ".join(power)
            + " Uma taxa de rejeição maior sob H₁ indica mais poder e deve ser avaliada junto "
            "ao erro tipo I sob H₀."
        )
        critical = cond.loc[~cond["normal_ok"], ["condition", "p0"]].drop_duplicates()
        for row in type1.merge(critical, on="condition").itertuples(index=False):
            st.markdown(
                f"**Q3 · Aproximação normal com n = {row.n}** · Sob H₀, são esperadas "
                f"{num(row.n * row.p0, 1)} falhas e {num(row.n * (1 - row.p0), 1)} sucessos. "
                "A menor contagem compromete a aproximação normal. Na simulação, o erro tipo I "
                f"foi de {pct(row.z_rate)} para o Z ({row.z_status}) e "
                f"{pct(row.binomial_rate)} para o binomial exato ({row.binomial_status}). "
                "A cauda binomial muda em saltos a cada falha adicional. Por isso, o menor "
                "número de falhas que permite rejeitar H₀ pode deixar o erro tipo I teórico abaixo de α."
            )
    st.markdown("### Recomendação")
    st.markdown(
        cfg.RECOMENDACAO + " Em amostras pequenas, esse controle pode vir acompanhado de menor poder."
    )
    st.markdown("### Limitações")
    st.markdown("\n".join(f"- {item}" for item in limitations(len(ctx["real"]))))


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
    if cfg.PROJECTS_URL:
        links.append(f"[GitHub Projects]({cfg.PROJECTS_URL})")
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
        st.subheader("Amostra simulada")
        st.caption(
            "Ajuste os dois tamanhos de amostra separadamente no G1. "
            "Só a primeira amostra alimenta o G2; G3/G4 permanecem oficiais e fixos."
        )
        n = st.number_input("G1/G2 · Amostra pequena (n)", min_value=5, max_value=1000, value=30, step=5)
        reference_n = st.number_input("G1 · Amostra de referência (n)", min_value=5, max_value=1000, value=G1_REFERENCE_N, step=5)
        true_p = st.slider("Probabilidade de falha na simulação", 0.0, 0.5, 0.10, 0.01)
        seed = st.number_input("Semente (G1/G2)", min_value=0, value=42, step=1)
        st.subheader("Hipóteses do G2")
        st.caption("Explore outra meta ou outro α no G2. O cenário oficial permanece em 5%.")
        p0 = st.slider("Meta p₀", 0.01, 0.20, cfg.P0, 0.01)
        alpha = st.select_slider("α", options=[0.01, 0.05, 0.10], value=cfg.ALPHA)

    ctx = build_context(
        int(n), float(true_p), int(seed), float(p0), float(alpha), int(reference_n)
    )
    for index, section in enumerate(SECTIONS):
        if index:
            st.divider()
        section(ctx)


if __name__ == "__main__":  # `streamlit run` e AppTest executam o script como __main__
    main()
