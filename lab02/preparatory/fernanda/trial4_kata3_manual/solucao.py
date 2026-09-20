"""Solução de referência técnica; não é uma execução oficial de Fernanda."""

from itertools import groupby


def compactar_leituras(
    leituras: list[int], limiar_repeticao: int = 3
) -> list[tuple[int, int]]:
    compactado = []
    for valor, grupo in groupby(leituras):
        quantidade = sum(1 for _ in grupo)
        if quantidade >= limiar_repeticao:
            compactado.append((valor, quantidade))
        else:
            compactado.extend((valor, 1) for _ in range(quantidade))
    return compactado


def descompactar(compactado: list[tuple[int, int]]) -> list[int]:
    return [valor for valor, quantidade in compactado for _ in range(quantidade)]
