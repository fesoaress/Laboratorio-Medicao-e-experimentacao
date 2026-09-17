from solucao import compactar_leituras, descompactar


def test_run_comprimida():
    assert compactar_leituras([5, 5, 5, 5, 7]) == [(5, 4), (7, 1)]


def test_run_abaixo_do_limiar_nao_comprime():
    assert compactar_leituras([5, 5, 7, 7, 7, 7]) == [(5, 1), (5, 1), (7, 4)]


def test_sem_repeticoes():
    assert compactar_leituras([1, 2, 3]) == [(1, 1), (2, 1), (3, 1)]


def test_lista_vazia():
    assert compactar_leituras([]) == []


def test_limiar_customizado():
    assert compactar_leituras([2, 2, 2], limiar_repeticao=4) == [(2, 1), (2, 1), (2, 1)]
    assert compactar_leituras([2, 2, 2, 2], limiar_repeticao=4) == [(2, 4)]


def test_toda_lista_e_uma_run():
    assert compactar_leituras([9, 9, 9, 9, 9]) == [(9, 5)]


def test_descompactar_simples():
    assert descompactar([(5, 4), (7, 1)]) == [5, 5, 5, 5, 7]


def test_descompactar_lista_vazia():
    assert descompactar([]) == []


def test_round_trip_varios_casos():
    casos = [
        [5, 5, 5, 5, 7],
        [1, 2, 3],
        [],
        [9, 9, 9, 9, 9],
        [1, 1, 2, 2, 2, 2, 3],
    ]
    for caso in casos:
        assert descompactar(compactar_leituras(caso)) == caso
