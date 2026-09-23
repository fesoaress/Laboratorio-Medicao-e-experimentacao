"""
KATA 4 — Manutenção Preditiva por Média Móvel

Contexto:
Uma máquina registra a temperatura de operação uma vez por dia. Quando a
média das últimas N leituras ultrapassa um limite de segurança, o dia deve
ser sinalizado como "precisa de manutenção".

Implemente `precisa_manutencao`, que recebe:
    - temperaturas: list[float]  -> uma leitura por dia, em ordem cronológica
    - limite: float              -> limite de segurança da média
    - janela: int                -> tamanho da janela de dias para a média móvel

E devolve list[int]: os ÍNDICES (0-based) dos dias em que a média móvel
ultrapassou (>) o limite.

Regra da janela no início da lista (quando ainda não há `janela` leituras
acumuladas): use quantas leituras já existirem até aquele índice (janela
"parcial"), em vez de pular esses dias.

Formalmente, para o índice i, a janela considerada é:
    temperaturas[max(0, i - janela + 1) : i + 1]
e o dia i é sinalizado se a média dessa janela for ESTRITAMENTE MAIOR que
`limite`.

Exemplos (janela=3, limite=50):
    temperaturas = [40, 45, 60, 60, 60]
    - i=0: média([40])          = 40.0  -> não sinaliza
    - i=1: média([40,45])       = 42.5  -> não sinaliza
    - i=2: média([40,45,60])    = 48.33 -> não sinaliza
    - i=3: média([45,60,60])    = 55.0  -> SINALIZA
    - i=4: média([60,60,60])    = 60.0  -> SINALIZA
    precisa_manutencao([40, 45, 60, 60, 60], 50, 3) -> [3, 4]

    precisa_manutencao([], 50, 3) -> []
"""


def precisa_manutencao(temperaturas: list[float], limite: float, janela: int) -> list[int]:
    dias_manutencao = []

    for i in range(len(temperaturas)):
        inicio = max(0, i - janela + 1)
        sub_lista = temperaturas[inicio : i + 1]

        media = sum(sub_lista) / len(sub_lista)

        if media > limite:
            dias_manutencao.append(i)

    return dias_manutencao
