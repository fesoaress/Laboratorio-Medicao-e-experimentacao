from pathlib import Path


# Raiz do repositório
BASE_DIR = Path(__file__).resolve().parents[2]

# Katas usados no experimento
KATAS_DIR = BASE_DIR / "src" / "katas"

# Diretório onde os dados dos trials serão armazenados
RESULTS_DIR = BASE_DIR / "lab02" / "trials" / "results"

# Diretório isolado onde cada participante edita sua cópia do kata.
WORKSPACES_DIR = BASE_DIR / "lab02" / "trials" / "workspaces"

# Cópias imutáveis do código no encerramento de cada trial.
FINAL_SOLUTIONS_DIR = RESULTS_DIR / "solutions"

# Arquivos de saída
TRIALS_CSV = RESULTS_DIR / "trials.csv"
CYCLES_CSV = RESULTS_DIR / "trial_cycles.csv"

# Time-box máximo definido pelo laboratório: 35 minutos
TIME_BOX_MINUTES = 35
TIME_BOX_SECONDS = TIME_BOX_MINUTES * 60

# Alocação definida para Islayder na S02. Os valores são canônicos e também
# são usados nas saídas CSV para permitir junção direta com as métricas RQ3.
ISLAYDER_ALLOCATION = {
    "kata1_normalizador_etiquetas": "IA",
    "kata2_balanceamento_turnos": "Manual",
    "kata3_compactador_sensor": "IA",
    "kata4_manutencao_preditiva": "Manual",
}
