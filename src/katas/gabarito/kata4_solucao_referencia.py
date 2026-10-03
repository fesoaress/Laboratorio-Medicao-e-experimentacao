def precisa_manutencao(temperaturas: list[float], limite: float, janela: int) -> list[int]:
    resultado = []
    for i in range(len(temperaturas)):
        inicio = max(0, i - janela + 1)
        subjanela = temperaturas[inicio:i + 1]
        media = sum(subjanela) / len(subjanela)
        if media > limite:
            resultado.append(i)
    return resultado
