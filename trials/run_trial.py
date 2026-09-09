import time

from config import TIME_BOX_SECONDS
from storage import registrar_ciclo, registrar_trial
from test_runner import executar_testes


def executar_trial(participante: str, kata: str, tratamento: str):
    inicio = time.monotonic()
    ciclo = 0

    ultimo_resultado = {
        "passando": 0,
        "falhando": 0,
        "total": 0,
        "taxa_sucesso": 0.0,
        "green": False,
    }

    print("\n=== Trial iniciado ===")
    print(f"Participante: {participante}")
    print(f"Kata: {kata}")
    print(f"Tratamento: {tratamento}")
    print("Time-box: 35 minutos")

    while True:
        tempo_decorrido = round(time.monotonic() - inicio, 2)

        if tempo_decorrido >= TIME_BOX_SECONDS:
            status = "time-box"
            break

        input(
            "\nPressione ENTER para executar os testes "
            "ou Ctrl+C para interromper o trial..."
        )

        ciclo += 1
        ultimo_resultado = executar_testes(kata)

        tempo_decorrido = round(time.monotonic() - inicio, 2)

        dados_ciclo = {
            "participante": participante,
            "kata": kata,
            "tratamento": tratamento,
            "ciclo": ciclo,
            "tempo_segundos": tempo_decorrido,
            "testes_passando": ultimo_resultado["passando"],
            "testes_falhando": ultimo_resultado["falhando"],
            "total_testes": ultimo_resultado["total"],
            "taxa_sucesso": ultimo_resultado["taxa_sucesso"],
        }

        registrar_ciclo(dados_ciclo)

        print(
            f"Ciclo {ciclo}: "
            f"{ultimo_resultado['passando']}/"
            f"{ultimo_resultado['total']} testes passando "
            f"({ultimo_resultado['taxa_sucesso']}%)"
        )

        if ultimo_resultado["green"]:
            status = "green"
            break

    tempo_final = min(
        round(time.monotonic() - inicio, 2),
        TIME_BOX_SECONDS,
    )

    dados_trial = {
        "participante": participante,
        "kata": kata,
        "tratamento": tratamento,
        "tempo_segundos": tempo_final,
        "testes_passando": ultimo_resultado["passando"],
        "testes_falhando": ultimo_resultado["falhando"],
        "total_testes": ultimo_resultado["total"],
        "taxa_sucesso": ultimo_resultado["taxa_sucesso"],
        "ciclos": ciclo,
        "status": status,
    }

    registrar_trial(dados_trial)

    print("\n=== Trial encerrado ===")
    print(f"Status: {status}")
    print(f"Tempo total: {tempo_final} segundos")
    print(f"Ciclos executados: {ciclo}")


def main():
    participante = input("Participante: ").strip()
    kata = input("Kata: ").strip()
    tratamento = input("Tratamento (IA/Manual): ").strip()

    executar_trial(
        participante=participante,
        kata=kata,
        tratamento=tratamento,
    )


if __name__ == "__main__":
    main()