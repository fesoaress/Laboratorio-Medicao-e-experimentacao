"""Textos curtos (2–4 frases) que acompanham cada gráfico; reaproveitáveis na entrega final."""

from lab04.src.plots import critical_k


def g1_caption(real_n: int, real_k: int, sim_n: int, sim_k: int, p0: float) -> str:
    return (
        f"Cada observação é binária (0 = sucesso, 1 = falha), então os histogramas são contagens de duas "
        f"categorias, não distribuições de tempos. Nos dados reais houve {real_k} falhas em {real_n} execuções "
        f"({real_k / real_n:.1%}); na amostra simulada, {sim_k} em {sim_n} ({sim_k / sim_n:.1%}). "
        f"A linha tracejada mostra a contagem esperada se a taxa fosse exatamente {p0:.0%}, a fronteira de H0."
    )


def g2_caption(res: dict) -> str:
    n, p0, alpha = res["n"], res["p0"], res["alpha"]
    k_crit = critical_k(n, p0, alpha)
    reg = f"K ≥ {k_crit}" if k_crit is not None else "vazia"
    decisao = "rejeitam" if (res["reject_z"] and res["reject_binomial"]) else (
        "não rejeitam" if not (res["reject_z"] or res["reject_binomial"]) else "chegam a decisões diferentes sobre")
    caution = (" Como n·p0 < 5 ou n·(1−p0) < 5, a aproximação normal do teste Z é pouco confiável aqui."
               if res["z_normal_approximation_caution"] else "")
    return (
        f"Os dois testes são unilaterais à direita: só valores altos de falhas contrariam H0 (p ≤ {p0:g}). "
        f"A área sombreada é o p-valor — Z: {res['z_p_value']:.4f}; binomial exato: {res['binomial_p_value']:.4f} — "
        f"e a hachura é a região de rejeição (binomial: {reg}). Com α = {alpha:g}, os testes {decisao} H0. "
        f"O p-valor é a probabilidade de ver resultado igual ou mais extremo supondo H0 verdadeira; "
        f"não é a probabilidade de H0 ser verdadeira.{caution}"
    )


def _thousands(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def _pct(x: float) -> str:
    return f"{100 * x:.2f}%".replace(".", ",")


def g3_caption(t1) -> str:
    """t1: saída de ``s02_results.type1_table`` (uma linha por condição)."""
    reps = _thousands(int(t1["repetitions"].iloc[0]))
    alpha = float(t1["alpha"].iloc[0])
    parts = []
    for r in t1.itertuples():
        parts.append(
            f"{r.condition}: Z {_pct(r.z_rate)} ({r.z_status}), binomial exato {_pct(r.binomial_rate)} ({r.binomial_status})"
        )
    se_max = max(t1["z_se"].max(), t1["binomial_se"].max())
    return (
        f"Taxa observada de rejeição quando H0 é verdadeira (p real = p0), em {reps} repetições simuladas por "
        f"condição, contra a linha de α = {_pct(alpha)}. "
        + "; ".join(parts) + ". "
        f"Classificamos como liberal ou conservador apenas quando a diferença para α excede 1,96 erros-padrão "
        f"de Monte Carlo (até {_pct(se_max)} aqui); os dados são simulados, não observações reais de CI."
    )


def g4_caption(pw, alpha: float) -> str:
    """pw: saída de ``s02_results.power_table``."""
    reps = _thousands(int(pw["repetitions"].iloc[0]))
    bits = []
    for cond, g in pw.groupby("condition", sort=False):
        d = (g["z_rate"] - g["binomial_rate"]).abs()
        i = d.idxmax()
        if d[i] == 0:
            bits.append(f"em {cond}, as taxas dos dois testes foram idênticas em todos os pontos (as curvas se sobrepõem)")
        else:
            bits.append(
                f"em {cond}, a maior diferença observada entre os testes foi "
                + f"{100 * d[i]:.1f}".replace(".", ",") + " pp "
                + f"(efeito de {g.loc[i, 'effect_pp']:g}".replace(".", ",") + " pp)"
            )
    return (
        f"Proporção de rejeições de cada teste conforme o tamanho do efeito (p real − p0, em pontos percentuais), "
        f"com {reps} repetições simuladas por ponto; no efeito 0 a curva é o erro tipo I. "
        + (lambda t: t[0].upper() + t[1:])("; ".join(bits)) + ". "
        "Quando um teste rejeita mais que α sob H0 (liberal), parte do seu poder aparente vem desse excesso, então "
        "as curvas só são diretamente comparáveis onde os erros tipo I são parecidos."
    )