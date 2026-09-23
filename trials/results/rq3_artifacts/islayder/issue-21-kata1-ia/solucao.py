"""Normalização de etiquetas de estoque."""

import re


PADRAO_ETIQUETA = re.compile(r"[A-Z]{2}-[0-9]{4}")


def normalizar_etiquetas(codigos: list[str]) -> list[str]:
    """Normaliza etiquetas válidas e marca as demais como inválidas."""
    resultado = []

    for codigo in codigos:
        normalizado = "".join(codigo.split()).upper()
        if re.fullmatch(r"[A-Z]{2}[0-9]{4}", normalizado):
            normalizado = f"{normalizado[:2]}-{normalizado[2:]}"

        if not PADRAO_ETIQUETA.fullmatch(normalizado):
            normalizado = "INVALIDO"
        resultado.append(normalizado)

    return resultado
