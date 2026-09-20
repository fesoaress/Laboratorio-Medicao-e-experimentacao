"""Solução de referência técnica; não é uma execução oficial de Fernanda."""


def minimo_transferencias(horas: list[int], capacidade_max: int) -> int:
    if sum(horas) > capacidade_max * len(horas):
        return -1
    return sum(max(0, hora - capacidade_max) for hora in horas)
