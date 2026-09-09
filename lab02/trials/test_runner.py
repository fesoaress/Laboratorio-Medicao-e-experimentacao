import re
import subprocess

from config import KATAS_DIR


def extrair_quantidade(saida: str, status: str) -> int:
    """
    Extrai da saída do pytest a quantidade de testes
    com determinado status, como 'passed' ou 'failed'.
    """
    resultado = re.search(rf"(\d+)\s+{status}", saida)

    if resultado:
        return int(resultado.group(1))

    return 0


def executar_testes(kata: str) -> dict:
    """
    Executa os testes automatizados de um kata
    e retorna um resumo dos resultados.
    """
    caminho_kata = KATAS_DIR / kata
    arquivo_teste = caminho_kata / "test_solucao.py"

    if not arquivo_teste.exists():
        raise FileNotFoundError(
            f"Arquivo de teste não encontrado: {arquivo_teste}"
        )

    processo = subprocess.run(
        ["python", "-m", "pytest", str(arquivo_teste), "-q"],
        capture_output=True,
        text=True,
    )

    saida = processo.stdout + processo.stderr

    passando = extrair_quantidade(saida, "passed")
    falhando = extrair_quantidade(saida, "failed")

    total = passando + falhando

    if total > 0:
        taxa_sucesso = round((passando / total) * 100, 2)
    else:
        taxa_sucesso = 0.0

    return {
        "passando": passando,
        "falhando": falhando,
        "total": total,
        "taxa_sucesso": taxa_sucesso,
        "green": total > 0 and falhando == 0,
    }