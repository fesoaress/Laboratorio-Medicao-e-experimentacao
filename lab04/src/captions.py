"""Textos curtos (2–4 frases) que acompanham cada gráfico; reaproveitáveis na entrega final."""

from lab04.src.conclusion import power_sentence
from lab04.src.formatting import pct, thousands


def g1_caption(real_n: int, real_k: int, sim_n: int, sim_k: int, p0: float) -> str:
    return (
        "Os histogramas mostram as frequências das duas categorias de uma variável binária, "
        "para a qual a noção usual de outlier de uma distribuição contínua fica fora do modelo. "
        f"Foram {real_k} falhas em {real_n} execuções reais ({pct(real_k / real_n)}) e "
        f"{sim_k} em {sim_n} execuções simuladas ({pct(sim_k / sim_n)}). "
        f"Os traços indicam {pct(1 - p0, 0)} de sucessos e {pct(p0, 0)} de falhas, as frequências "
        "esperadas na fronteira de H₀."
    )


def g2_caption(res: dict) -> str:
    caution = (
        " As contagens esperadas são pequenas para a aproximação normal."
        if res["z_normal_approximation_caution"] else ""
    )
    return (
        "Na fronteira p = p₀, o binomial exato soma as probabilidades das contagens a partir "
        "do K observado, enquanto o teste Z aproxima a cauda pela normal. "
        "O preenchimento marca a cauda do p-valor e a hachura mostra a região de rejeição "
        "definida por α. Uma seta indica quando a estatística observada fica fora do eixo exibido."
        f"{caution}"
    )


def g3_caption(t1) -> str:
    """t1: saída de ``s02_results.type1_table`` (uma linha por condição)."""
    reps = thousands(int(t1["repetitions"].iloc[0]))
    alpha = float(t1["alpha"].iloc[0])
    parts = []
    for r in t1.itertuples():
        parts.append(
            f"Em n = {r.n}, Z {pct(r.z_rate)} ({r.z_status}) e binomial exato "
            f"{pct(r.binomial_rate)} ({r.binomial_status})"
        )
    return (
        f"Comparamos as rejeições sob H₀ com α = {pct(alpha)}, usando {reps} ensaios simulados por condição. "
        + ". ".join(parts)
        + ". As hastes mostram ±1,96 erros-padrão estimados de Monte Carlo, e uma taxa é compatível "
        "com α quando a diferença fica dentro dessa margem calculada sob α."
    )


def g4_caption(pw) -> str:
    """pw: saída de ``s02_results.power_table``."""
    reps = thousands(int(pw["repetitions"].iloc[0]))
    findings = []
    for _, group in pw.sort_values(["n", "effect_pp"]).groupby("condition", sort=False):
        positive = group[group["effect_pp"] > 1e-8]
        example = ""
        if not positive.empty:
            point = positive.iloc[0]
            effect = f"{point['effect_pp']:g}".replace(".", ",")
            example = f" (a {effect} p.p., Z {pct(point['z_rate'])} e binomial {pct(point['binomial_rate'])})"
        findings.append(f"Em n = {int(group['n'].iloc[0])}, {power_sentence(group)}{example}.")
    return (
        f"Cada ponto usa {reps} repetições simuladas, com o efeito medido em pontos percentuais acima de p₀. "
        "No efeito zero, a taxa de rejeição estima o erro tipo I. "
        + " ".join(findings)
    )
