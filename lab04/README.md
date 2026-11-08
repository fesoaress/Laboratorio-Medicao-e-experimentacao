# Lab04 — Testes de hipótese por dentro (P4: Z para proporção × binomial exato)

Cenário: a taxa de falha de execuções de CI (GitHub Actions) ultrapassa a meta de 5%?
H0: p ≤ 0,05 · H1: p > 0,05 (unilateral à direita) · α = 0,05 · 0 = sucesso, 1 = falha.

## Instalação

```bash
python3 -m venv .venv && source .venv/bin/activate
python -m pip install -r lab04/requirements.txt
```

## Executar o dashboard (um comando, a partir da raiz do repositório)

```bash
streamlit run lab04/app.py
```

## Testes automatizados

```bash
python -m pytest -q lab04/tests
```

## Reproduzir os dados e as simulações

| Etapa | Comando | Saída |
|---|---|---|
| Coleta dos dados reais (Issue #77) | `python -m lab04.src.collect_ci_runs` | `lab04/data/ci_runs.csv` |
| Q1/Q2 (Issue #81) | `python -m lab04.src.s02_experiments` | `lab04/results/s02_q1_q2.csv` |
| Q3 (Issue #82) | ver `lab04/src/robustness.py` | `lab04/results/s02_q3.csv` |

O dashboard lê essas tabelas; G3/G4 aparecem conforme os arquivos existirem. Para apontar para
outra pasta de resultados: `LAB04_RESULTS_DIR=/caminho streamlit run lab04/app.py`.

## Itens que o grupo precisa preencher antes da entrega

Em `lab04/src/delivery_config.py`: `DASHBOARD_URL`, `REPO_URL`, `EXPECTATIVA_PREVIA` e
`RECOMENDACAO`. Enquanto estiverem vazios, o dashboard mostra uma caixa de pendências no topo
e avisos na seção 7. Quando todos estiverem preenchidos, os avisos desaparecem.

## Smoke test da entrega

```bash
python -m pytest -q lab04/tests/test_final_dashboard.py
```

Confere a ordem das sete seções, a presença das legendas, a tabela dos dados reais e a ausência de
`provisional_ci_runs.csv`.

## Seções do dashboard (ordem do enunciado)

1. Cenário · 2. Os dados (G1) · 3. Como os testes funcionam (G2) · 4. Erro tipo I (G3) ·
5. Poder (G4) · 6. Dados reais (tabela) · 7. Conclusão

## Estrutura do dashboard

| Arquivo | Conteúdo |
|---|---|
| `lab04/app.py` | Dashboard Streamlit; seções registradas em `SECTIONS` |
| `lab04/src/plots.py` | `plot_g1`, `plot_g2`, `plot_g3`, `plot_g4`; cor fixa por teste (Z azul, binomial laranja) |
| `lab04/src/captions.py` | Textos de 2–4 frases por gráfico (G3/G4 calculados a partir das tabelas) |
| `lab04/src/s02_results.py` | Validação e preparo das tabelas de Q1/Q2/Q3 |
| `lab04/src/real_results.py` | Tabela e decisão da seção 6 (testes sobre os dados reais, Issue #85) |
| `lab04/src/real_summary.py` | Tamanho do efeito na seção 6 (h de Cohen e IC exato de 95%) |
| `lab04/src/conclusion.py` | Achados de G3/G4 calculados das tabelas e ressalvas da seção 7 |
| `lab04/src/delivery_config.py` | Links e textos que só o grupo pode preencher |
| `lab04/src/formatting.py` | Formatação em português (vírgula decimal) |
| `lab04/src/data_adapter.py` | Carrega `lab04/data/ci_runs.csv` via `real_data.load_ci_runs` |

Dados **reais** (G1, seção 1 e 6) e dados **simulados** (G1 à direita, G2, G3, G4) são sempre
rotulados; os resultados de Monte Carlo não usam observações reais.

## Reprodutibilidade

Semente fixa (padrão 42); a mesma entrada gera os mesmos gráficos.