from pathlib import Path


# Raiz do repositório
BASE_DIR = Path(__file__).resolve().parents[2]

# Katas usados no experimento
KATAS_DIR = BASE_DIR / "src" / "katas"

# Diretório onde os dados dos trials serão armazenados
RESULTS_DIR = BASE_DIR / "lab02" / "trials" / "results"

# Arquivos de saída
TRIALS_CSV = RESULTS_DIR / "trials.csv"
CYCLES_CSV = RESULTS_DIR / "trial_cycles.csv"

# Time-box máximo definido pelo laboratório: 35 minutos
TIME_BOX_MINUTES = 35
TIME_BOX_SECONDS = TIME_BOX_MINUTES * 60