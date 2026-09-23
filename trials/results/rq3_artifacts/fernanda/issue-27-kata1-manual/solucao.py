"""Artefato estrutural reconstruído do código preparatório versionado."""

import re


FORMATO_ETIQUETA = re.compile(r"[A-Z]{2}-[0-9]{4}")
FORMATO_SEM_HIFEN = re.compile(r"[A-Z]{2}[0-9]{4}")


def normalizar_etiquetas(codigos: list[str]) -> list[str]:
    normalizados = []
    for codigo in codigos:
        normalizado = "".join(codigo.split()).upper()
        if FORMATO_SEM_HIFEN.fullmatch(normalizado):
            normalizado = f"{normalizado[:2]}-{normalizado[2:]}"
        normalizados.append(
            normalizado if FORMATO_ETIQUETA.fullmatch(normalizado) else "INVALIDO"
        )
    return normalizados
