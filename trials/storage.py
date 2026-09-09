import csv

from config import RESULTS_DIR, TRIALS_CSV, CYCLES_CSV


TRIAL_FIELDS = [
    "participante",
    "kata",
    "tratamento",
    "tempo_segundos",
    "testes_passando",
    "testes_falhando",
    "total_testes",
    "taxa_sucesso",
    "ciclos",
    "status",
]

CYCLE_FIELDS = [
    "participante",
    "kata",
    "tratamento",
    "ciclo",
    "tempo_segundos",
    "testes_passando",
    "testes_falhando",
    "total_testes",
    "taxa_sucesso",
]


def garantir_arquivos():
    """
    Cria a pasta de resultados e os CSVs com cabeçalho,
    caso ainda não existam.
    """
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    if not TRIALS_CSV.exists():
        _criar_csv(TRIALS_CSV, TRIAL_FIELDS)

    if not CYCLES_CSV.exists():
        _criar_csv(CYCLES_CSV, CYCLE_FIELDS)


def _criar_csv(caminho, campos):
    with caminho.open("w", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(arquivo, fieldnames=campos)
        writer.writeheader()


def registrar_trial(dados: dict):
    """
    Registra o resultado final de um trial.
    """
    garantir_arquivos()

    with TRIALS_CSV.open("a", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(
            arquivo,
            fieldnames=TRIAL_FIELDS,
        )
        writer.writerow(dados)


def registrar_ciclo(dados: dict):
    """
    Registra uma execução intermediária dos testes.
    """
    garantir_arquivos()

    with CYCLES_CSV.open("a", newline="", encoding="utf-8") as arquivo:
        writer = csv.DictWriter(
            arquivo,
            fieldnames=CYCLE_FIELDS,
        )
        writer.writerow(dados)