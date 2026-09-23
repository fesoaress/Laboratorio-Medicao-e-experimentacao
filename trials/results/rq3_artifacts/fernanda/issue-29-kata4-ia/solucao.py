"""Artefato estrutural reconstruído do código preparatório versionado."""


def precisa_manutencao(
    temperaturas: list[float], limite: float, janela: int
) -> list[int]:
    if janela <= 0:
        raise ValueError("janela deve ser positiva")

    alertas = []
    soma_janela = 0.0
    for indice, temperatura in enumerate(temperaturas):
        soma_janela += temperatura
        if indice >= janela:
            soma_janela -= temperaturas[indice - janela]
        tamanho_atual = min(indice + 1, janela)
        if soma_janela / tamanho_atual > limite:
            alertas.append(indice)
    return alertas
