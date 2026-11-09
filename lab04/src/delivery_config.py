"""Parâmetros do cenário oficial e links de entrega do Lab04."""

P0 = 0.05
ALPHA = 0.05
DASHBOARD_URL: str | None = "https://lab04-medicao-pucminas.streamlit.app/"
REPO_URL = "https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao"
PROJECTS_URL: str | None = None

# Expectativa metodológica registrada na S01 e retomada no roteiro de Fernanda.
EXPECTATIVA_PREVIA = (
    "Na S01, esperava-se que o Z fosse uma aproximação pior quando o número esperado de falhas "
    "fosse pequeno. Para a amostra maior, a expectativa era de maior concordância entre os testes."
)
RECOMENDACAO = (
    "Para investigar falhas raras no workflow, prefira o binomial exato, sobretudo com poucas "
    "falhas esperadas sob H₀. Sob o modelo binomial, ele mantém o erro tipo I no máximo em α. "
    "O Z pode ser uma aproximação útil quando as contagens esperadas de falhas e sucessos são maiores."
)
