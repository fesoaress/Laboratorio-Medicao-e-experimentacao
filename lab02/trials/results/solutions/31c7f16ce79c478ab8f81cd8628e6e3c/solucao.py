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
