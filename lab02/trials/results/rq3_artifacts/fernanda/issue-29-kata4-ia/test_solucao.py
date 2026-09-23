from solucao import precisa_manutencao


def test_caso_do_enunciado():
    assert precisa_manutencao([40, 45, 60, 60, 60], 50, 3) == [3, 4]


def test_lista_vazia():
    assert precisa_manutencao([], 50, 3) == []


def test_nenhum_dia_sinalizado():
    assert precisa_manutencao([10, 20, 15, 5], 100, 3) == []


def test_todos_os_dias_sinalizados():
    assert precisa_manutencao([90, 90, 90, 90], 50, 2) == [0, 1, 2, 3]


def test_janela_maior_que_lista():
    assert precisa_manutencao([60, 60, 60], 50, 10) == [0, 1, 2]


def test_janela_igual_a_um():
    assert precisa_manutencao([10, 60, 10, 60], 50, 1) == [1, 3]


def test_media_exatamente_no_limite_nao_sinaliza():
    assert precisa_manutencao([50, 50, 50], 50, 3) == []
    assert precisa_manutencao([50, 50, 50.0001], 50, 3) == [2]
