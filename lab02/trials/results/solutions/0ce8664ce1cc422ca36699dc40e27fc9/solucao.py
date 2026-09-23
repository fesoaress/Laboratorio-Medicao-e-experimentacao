"""
KATA 2 — Balanceamento de Turnos

Contexto:
Cada funcionário de uma equipe tem uma quantidade de horas alocadas na semana.
A empresa define uma capacidade máxima de horas por funcionário. Quando algum
funcionário ultrapassa esse limite, é preciso transferir horas dele para
funcionários que estão abaixo do limite, uma hora por vez.

Implemente `minimo_transferencias`, que recebe:
    - horas: list[int]        -> horas atuais de cada funcionário
    - capacidade_max: int     -> limite máximo de horas por funcionário

E devolve um int: o número MÍNIMO de transferências de 1 hora necessárias
para que TODOS os funcionários fiquem com horas <= capacidade_max,
considerando que:

    - O total de horas da equipe é fixo (transferir não cria nem destroi
      horas, só move de um funcionário para outro).
    - Uma transferência move exatamente 1 hora de um funcionário
      (que está acima ou no limite) para outro (que está abaixo do limite).
    - Se a soma total de horas for maior do que `capacidade_max * len(horas)`,
      não existe solução possível mesmo movendo todas as horas — nesse caso,
      devolva -1.
    - Se já estiver tudo dentro do limite, devolva 0.

Dica de raciocínio: o número mínimo de transferências é igual à soma do
excedente de todos os funcionários que estão ACIMA do limite (não precisa
simular fila por fila, já que cada hora movida de quem está acima resolve
exatamente 1 unidade de excedente).

Exemplos:
    minimo_transferencias([44, 40, 36], 40)   -> 4   (44 tem 4h de excedente)
    minimo_transferencias([40, 40, 40], 40)   -> 0
    minimo_transferencias([50, 50, 50], 40)   -> -1  (150 > 40*3=120)
    minimo_transferencias([48, 32], 40)       -> 8
"""


def minimo_transferencias(horas: list[int], capacidade_max: int) -> int:
    # Verifica se a soma total de horas é maior que a capacidade total da equipe
    if sum(horas) > capacidade_max * len(horas):
        return -1
    
    # Soma o excedente de cada funcionário que está acima do limite
    total_transferencias = sum(h - capacidade_max for h in horas if h > capacidade_max)
    
    return total_transferencias