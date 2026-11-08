"""Formatação em português (vírgula decimal, milhar com ponto) usada nos textos do dashboard."""


def thousands(n: int) -> str:
    return f"{n:,}".replace(",", ".")


def pct(x: float, digits: int = 2) -> str:
    return f"{100 * x:.{digits}f}%".replace(".", ",")


def num(x: float, digits: int = 2) -> str:
    return f"{x:.{digits}f}".replace(".", ",")


def pp(x_pp: float, digits: int = 1) -> str:
    return f"{x_pp:.{digits}f}".replace(".", ",") + " pp"