"""
KATA 1 — Normalizador de Etiquetas de Estoque

Contexto:
Um sistema de estoque recebe códigos de etiqueta digitados manualmente por
operadores, com formatação inconsistente. O formato correto de uma etiqueta é:

    duas letras + hífen + quatro dígitos   (ex: "AB-1234")

Implemente a função `normalizar_etiquetas`, que recebe uma lista de strings
"sujas" e devolve uma nova lista, na MESMA ORDEM, aplicando as regras:

1. Remover espaços em branco no início e no fim da string.
2. Remover espaços internos (ex: "ab 1234" -> "ab1234").
3. Converter as letras para maiúsculas.
4. Se a etiqueta tiver as duas letras e os quatro dígitos mas SEM hífen,
   inserir o hífen na posição correta (ex: "AB1234" -> "AB-1234").
5. Após aplicar as regras acima, validar se o resultado final bate exatamente
   com o padrão "AA-9999" (2 letras maiúsculas, hífen, 4 dígitos).
   - Se for válido, mantenha o valor normalizado.
   - Se NÃO for válido (letras/dígitos a mais ou a menos, caracteres
     inválidos, etc.), substitua o item por "INVALIDO" no lugar dele na lista
     de saída (não remova o item, apenas substitua).

Exemplos:
    normalizar_etiquetas(["ab-1234"])       -> ["AB-1234"]
    normalizar_etiquetas([" ab 1234 "])     -> ["AB-1234"]
    normalizar_etiquetas(["AB1234"])        -> ["AB-1234"]
    normalizar_etiquetas(["A-1234"])        -> ["INVALIDO"]   (só 1 letra)
    normalizar_etiquetas(["AB-12345"])      -> ["INVALIDO"]   (5 dígitos)
    normalizar_etiquetas(["ab-12a4"])       -> ["INVALIDO"]   (letra no lugar de dígito)
"""
import re

PADRAO = re.compile(r"^[A-Z]{2}-\d{4}$")

def normalizar_etiquetas(codigos: list[str]) -> list[str]:
    resultado = []
    for codigo in codigos:
        limpo = codigo.strip().replace(" ", "").upper()
        if len(limpo) == 6 and limpo[:2].isalpha() and limpo[2:].isdigit():
            limpo = f"{limpo[:2]}-{limpo[2:]}"
        if PADRAO.match(limpo):
            resultado.append(limpo)
        else:
            resultado.append("INVALIDO")
    return resultado
