def minimo_transferencias(horas: list[int], capacidade_max: int) -> int:
    if sum(horas) > capacidade_max * len(horas):
        return -1
    return sum(h - capacidade_max for h in horas if h > capacidade_max)
