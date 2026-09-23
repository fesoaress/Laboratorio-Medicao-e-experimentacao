from itertools import groupby


def compactar_leituras(leituras: list[int], limiar_repeticao: int = 3) -> list[tuple[int, int]]:
    resultado = []
    for valor, grupo in groupby(leituras):
        tamanho = len(list(grupo))
        if tamanho >= limiar_repeticao:
            resultado.append((valor, tamanho))
        else:
            resultado.extend((valor, 1) for _ in range(tamanho))
    return resultado


def descompactar(compactado: list[tuple[int, int]]) -> list[int]:
    resultado = []
    for valor, quantidade in compactado:
        resultado.extend([valor] * quantidade)
    return resultado
