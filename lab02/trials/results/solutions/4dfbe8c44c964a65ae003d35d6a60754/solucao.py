def compactar_leituras(leituras: list[int], limiar_repeticao: int = 3) -> list[tuple[int, int]]:
    if not leituras:
        return []
    resultado: list[tuple[int, int]] = []
    indice = 0
    while indice < len(leituras):
        valor = leituras[indice]
        fim = indice
        while fim + 1 < len(leituras) and leituras[fim + 1] == valor:
            fim += 1
        tamanho = fim - indice + 1
        if tamanho >= limiar_repeticao:
            resultado.append((valor, tamanho))
        else:
            resultado.extend((valor, 1) for _ in range(tamanho))
        indice = fim + 1
    return resultado


def descompactar(compactado: list[tuple[int, int]]) -> list[int]:
    expandido: list[int] = []
    for valor, quantidade in compactado:
        expandido.extend([valor] * quantidade)
    return expandido
