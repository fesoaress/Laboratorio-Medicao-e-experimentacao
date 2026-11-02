"""Textos curtos (2–4 frases) que acompanham cada gráfico; reaproveitáveis na entrega final."""

from lab04.src.plots import critical_k


def g1_caption(real_n: int, real_k: int, sim_n: int, sim_k: int, p0: float, provisional: bool) -> str:
    prov = (" ATENÇÃO: os dados reais exibidos são PROVISÓRIOS e serão substituídos pela coleta da Issue #77."
            if provisional else "")
    return (
        f"Cada observação é binária (0 = sucesso, 1 = falha), então os histogramas são contagens de duas "
        f"categorias, não distribuições de tempos. Nos dados reais houve {real_k} falhas em {real_n} execuções "
        f"({real_k / real_n:.1%}); na amostra simulada, {sim_k} em {sim_n} ({sim_k / sim_n:.1%}). "
        f"A linha tracejada mostra a contagem esperada se a taxa fosse exatamente {p0:.0%}, a fronteira de H0.{prov}"
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