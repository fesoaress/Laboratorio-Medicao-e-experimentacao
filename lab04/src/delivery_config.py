"""Itens que SÓ O GRUPO pode preencher antes da entrega final (Issue #84).

Enquanto estiverem como None, o dashboard mostra uma caixa de pendências no topo e avisos
nas seções correspondentes. Nada aqui deve ser escrito sem a decisão do grupo.
"""

# Links exigidos no topo do dashboard (enunciado, seção 4).
DASHBOARD_URL: str | None = None   # ex.: "https://<app>.streamlit.app"
REPO_URL: str | None = None        # ex.: "https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao"

# Seção 7 — escritas pelo grupo (o enunciado pede o que o grupo ESPERAVA antes de simular).
EXPECTATIVA_PREVIA: str | None = None   # qual teste o grupo esperava que se saísse melhor, e por quê
RECOMENDACAO: str | None = None         # qual teste usar no cenário e quando a escolha mudaria


def pending_items() -> list[str]:
    items = []
    if not DASHBOARD_URL:
        items.append("link do dashboard (DASHBOARD_URL)")
    if not REPO_URL:
        items.append("link do repositório / GitHub Projects (REPO_URL)")
    if not EXPECTATIVA_PREVIA:
        items.append("expectativa prévia do grupo (EXPECTATIVA_PREVIA)")
    if not RECOMENDACAO:
        items.append("recomendação do grupo (RECOMENDACAO)")
    return items