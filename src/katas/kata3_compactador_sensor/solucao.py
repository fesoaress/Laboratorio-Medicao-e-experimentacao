"""
KATA 3 — Compactador de Leituras de Sensor

Contexto:
Um sensor industrial registra uma leitura por segundo. Para economizar
espaço de armazenamento, queremos compactar sequências de leituras
IDÊNTICAS e CONSECUTIVAS, mas só vale a pena compactar quando a repetição
é "significativa": uma run de tamanho >= `limiar_repeticao`.

Implemente duas funções:

1. `compactar_leituras(leituras: list[int], limiar_repeticao: int = 3) -> list[tuple[int, int]]`

   Percorre a lista da esquerda para a direita e agrupa leituras iguais e
   consecutivas (runs). Para cada run:
     - Se o tamanho da run for >= limiar_repeticao, gera UMA tupla
       (valor, quantidade) representando toda a run.
     - Se o tamanho da run for < limiar_repeticao, cada leitura da run vira
       sua própria tupla (valor, 1) (ou seja, NÃO comprime).

   A ordem das tuplas na saída deve refletir a ordem original das leituras.

2. `descompactar(compactado: list[tuple[int, int]]) -> list[int]`

   Função inversa: expande cada tupla (valor, quantidade) de volta para
   `quantidade` cópias de `valor`, na ordem em que aparecem.
   (Note que `descompactar(compactar_leituras(x))` deve devolver `x`
   novamente, para qualquer x e qualquer limiar.)

Exemplos (limiar_repeticao=3):
    compactar_leituras([5, 5, 5, 5, 7])       -> [(5, 4), (7, 1)]
    compactar_leituras([5, 5, 7, 7, 7, 7])    -> [(5, 1), (5, 1), (7, 4)]
    compactar_leituras([1, 2, 3])             -> [(1, 1), (2, 1), (3, 1)]
    compactar_leituras([])                    -> []

    descompactar([(5, 4), (7, 1)])            -> [5, 5, 5, 5, 7]
"""


def compactar_leituras(leituras: list[int], limiar_repeticao: int = 3) -> list[tuple[int, int]]:
    # TODO: implementar
    raise NotImplementedError


def descompactar(compactado: list[tuple[int, int]]) -> list[int]:
    # TODO: implementar
    raise NotImplementedError
