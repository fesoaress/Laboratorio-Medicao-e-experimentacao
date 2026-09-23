"""Compactação e descompactação de leituras consecutivas."""


def compactar_leituras(
    leituras: list[int], limiar_repeticao: int = 3
) -> list[tuple[int, int]]:
    """Compacta runs que alcançam o limiar informado."""
    if not leituras:
        return []

    compactado = []
    valor_atual = leituras[0]
    quantidade = 1

    for valor in leituras[1:]:
        if valor == valor_atual:
            quantidade += 1
            continue

        compactado.extend(_representar_run(valor_atual, quantidade, limiar_repeticao))
        valor_atual = valor
        quantidade = 1

    compactado.extend(_representar_run(valor_atual, quantidade, limiar_repeticao))
    return compactado


def _representar_run(
    valor: int, quantidade: int, limiar_repeticao: int
) -> list[tuple[int, int]]:
    if quantidade >= limiar_repeticao:
        return [(valor, quantidade)]
    return [(valor, 1)] * quantidade


def descompactar(compactado: list[tuple[int, int]]) -> list[int]:
    """Expande cada par em sua sequência original de leituras."""
    leituras = []
    for valor, quantidade in compactado:
        leituras.extend([valor] * quantidade)
    return leituras
