from solucao import normalizar_etiquetas


def test_ja_valido_minusculo():
    assert normalizar_etiquetas(["ab-1234"]) == ["AB-1234"]


def test_espacos_nas_bordas():
    assert normalizar_etiquetas([" ab-1234 "]) == ["AB-1234"]


def test_espaco_interno_sem_hifen():
    assert normalizar_etiquetas(["ab 1234"]) == ["AB-1234"]


def test_sem_hifen():
    assert normalizar_etiquetas(["AB1234"]) == ["AB-1234"]


def test_uma_letra_invalida():
    assert normalizar_etiquetas(["A-1234"]) == ["INVALIDO"]


def test_cinco_digitos_invalido():
    assert normalizar_etiquetas(["AB-12345"]) == ["INVALIDO"]


def test_letra_no_lugar_de_digito():
    assert normalizar_etiquetas(["ab-12a4"]) == ["INVALIDO"]


def test_string_vazia_invalida():
    assert normalizar_etiquetas([""]) == ["INVALIDO"]


def test_lista_mista_preserva_ordem():
    entrada = ["ab-1234", "xy9999", "  z-1", "cd-5678"]
    esperado = ["AB-1234", "XY-9999", "INVALIDO", "CD-5678"]
    assert normalizar_etiquetas(entrada) == esperado


def test_lista_vazia():
    assert normalizar_etiquetas([]) == []
