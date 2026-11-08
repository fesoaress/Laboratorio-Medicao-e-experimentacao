"""Textos curtos (2–4 frases) que acompanham cada gráfico; reaproveitáveis na entrega final."""

from lab04.src.conclusion import power_sentence
from lab04.src.formatting import num as _num, pct as _pct, thousands as _thousands
from lab04.src.formatting import p_value
from lab04.src.plots import critical_k


def g1_caption(real_n: int, real_k: int, sim_n: int, sim_k: int, p0: float) -> str:
    return (
        f"Cada observação é binária (0 = sucesso, 1 = falha), então os histogramas são contagens de duas "
        f"categorias, não distribuições de tempos. Nos dados reais houve {real_k} falhas em {real_n} execuções "
        f"({_pct(real_k / real_n, 1)}); na amostra simulada, {sim_k} em {sim_n} ({_pct(sim_k / sim_n, 1)}). "
        f"A linha tracejada mostra a contagem esperada se a taxa fosse exatamente {_pct(p0, 0)}, a fronteira de H0."
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
        f"Os dois testes são unilaterais à direita: só valores altos de falhas contrariam H0 (p ≤ {_num(p0)}). "
        f"O sombreado mostra a cauda do p-valor (Z {p_value(res['z_p_value'])}, binomial exato "
        f"{p_value(res['binomial_p_value'])}) e a hachura marca a região de rejeição (binomial {reg}). "
        f"Com α = {_num(alpha)}, os testes {decisao} H0. "
        f"Calculamos o p-valor na fronteira p = p₀ como a probabilidade de observar um resultado "
        f"igual ou mais extremo à direita, usando a aproximação normal no Z.{caution}"
    )


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
        f"Nos dados simulados, comparamos as taxas de rejeição sob H₀ (p = p₀) com α = {_pct(alpha)}, "
        f"usando {reps} repetições por condição. "
        + ". ".join(parts) + ". "
        f"As barras mostram ±1,96 erros-padrão estimados de Monte Carlo (EP de até {_pct(se_max)}). "
        "A classificação compara a diferença para α com 1,96 erros-padrão calculados sob α."
    )


def g4_caption(pw, alpha: float) -> str:
    """pw: saída de ``s02_results.power_table``."""
    reps = _thousands(int(pw["repetitions"].iloc[0]))
    bits = [f"em {cond}, {power_sentence(g)}" for cond, g in pw.groupby("condition", sort=False)]
    return (
        f"Proporção de rejeições de cada teste conforme o tamanho do efeito (p real − p0, em pontos percentuais), "
        f"com {reps} repetições simuladas por ponto; no efeito 0 a curva é o erro tipo I. "
        + (lambda t: t[0].upper() + t[1:])("; ".join(bits)) + ". "
        "Em condições com diferentes taxas de erro tipo I, uma regra mais liberal pode elevar o poder "
        "à custa de mais falsos alarmes."
    )
