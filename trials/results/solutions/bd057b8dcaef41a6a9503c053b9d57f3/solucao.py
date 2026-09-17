def precisa_manutencao(temperaturas: list[float], limite: float, janela: int) -> list[int]:
    alertas = []
    for indice, _ in enumerate(temperaturas):
        inicio = max(0, indice - janela + 1)
        janela_atual = temperaturas[inicio : indice + 1]
        media = sum(janela_atual) / len(janela_atual)
        if media > limite:
            alertas.append(indice)
    return alertas
