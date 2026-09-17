from solucao import minimo_transferencias


def test_caso_basico():
    assert minimo_transferencias([44, 40, 36], 40) == 4


def test_ja_balanceado():
    assert minimo_transferencias([40, 40, 40], 40) == 0


def test_impossivel():
    assert minimo_transferencias([50, 50, 50], 40) == -1


def test_dois_funcionarios():
    assert minimo_transferencias([48, 32], 40) == 8


def test_todos_abaixo_do_limite():
    assert minimo_transferencias([10, 20, 30], 40) == 0


def test_um_unico_funcionario_no_limite():
    assert minimo_transferencias([40], 40) == 0


def test_um_unico_funcionario_acima_impossivel():
    assert minimo_transferencias([45], 40) == -1


def test_multiplos_acima_do_limite():
    assert minimo_transferencias([50, 45, 10, 15], 40) == 15


def test_no_limite_exato_do_total():
    # soma == capacidade_max * n, tecnicamente possível
    assert minimo_transferencias([60, 20, 40], 40) == 20
