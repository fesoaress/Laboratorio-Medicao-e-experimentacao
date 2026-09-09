"""Exemplo didático da S01 — validação das métricas estruturais (RQ3).

Este arquivo NÃO é um kata do experimento. Serve para conferir manualmente
se Radon/jscpd e o script run_metrics.py estão coerentes.

Complexidade ciclomática (McCabe), contagem manual:
  - CC = 1 (caminho base) + 1 por decisão (if/elif/for/while/and/or/...)

  sinal            -> if + elif              => CC = 3
  soma_positiva    -> for + if               => CC = 3
  formatar_bloco_a -> sem decisões           => CC = 1
  formatar_bloco_b -> sem decisões           => CC = 1

  média esperada = (3 + 3 + 1 + 1) / 4 = 2.0

Duplicação:
  formatar_bloco_a e formatar_bloco_b têm corpos propositalmente iguais
  (>= 5 linhas), para o jscpd detectar clone com a config fixa do lab.
"""


def sinal(n: int) -> str:
    if n > 0:
        return "positivo"
    elif n < 0:
        return "negativo"
    else:
        return "zero"


def soma_positiva(valores: list[int]) -> int:
    total = 0
    for valor in valores:
        if valor > 0:
            total += valor
    return total


def formatar_bloco_a(nome: str, idade: int, cidade: str) -> str:
    linha1 = f"nome={nome}"
    linha2 = f"idade={idade}"
    linha3 = f"cidade={cidade}"
    linha4 = f"chave={nome}-{idade}"
    linha5 = f"resumo={nome}/{cidade}/{idade}"
    return "|".join([linha1, linha2, linha3, linha4, linha5])


def formatar_bloco_b(nome: str, idade: int, cidade: str) -> str:
    linha1 = f"nome={nome}"
    linha2 = f"idade={idade}"
    linha3 = f"cidade={cidade}"
    linha4 = f"chave={nome}-{idade}"
    linha5 = f"resumo={nome}/{cidade}/{idade}"
    return "|".join([linha1, linha2, linha3, linha4, linha5])
