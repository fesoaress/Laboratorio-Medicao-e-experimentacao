# Lab02 S03 — Vinicius (Dashboard)

**Issue:** #35 — Consolidação de RQ1, RQ2, RQ3 e inovação num dashboard único.
**Responsabilidade:** consumir as tabelas geradas pelas análises de RQ1/RQ2/RQ3, padronizar as visualizações e entregar um painel consolidado, usado como Figura 8 do relatório final do grupo (seções 3.6, 4.2 e 4.3).

## O que foi entregue

- `lab02/dashboard/build_dashboard.py`: script que lê os CSVs consolidados de RQ1, RQ2, RQ3 e inovação e gera um painel único, executável com:
  ```bash
  python -m lab02.dashboard.build_dashboard
  ```
- `reports/figures/dashboard_final.png`: saída do script, publicada como **Figura 8** do relatório final ("Dashboard final das questões de pesquisa e da inovação").

## Composição do painel

O dashboard reúne, num único artefato, quatro KPIs de topo e seis subplots:

**KPIs de topo:**
- Número total de trials finais (12)
- Número de participantes (3)
- Mediana de tempo até green por tratamento (IA: 112,50 s · Manual: 209,01 s)
- Testes finais passando (105/105)
- Duplicação de código detectada (0%)

**Subplots (2×3):**
1. RQ1 — tempo até green por tratamento (boxplot com pontos individuais)
2. RQ2 — testes finais aprovados (barra horizontal, IA 54/54 · Manual 51/51)
3. Inovação — retrabalho / ciclo em que cada trial atingiu green
4. RQ3 — distribuição de LOC lógico por tratamento
5. RQ3 — distribuição de complexidade ciclomática média por tratamento
6. RQ3 — dispersão LOC × complexidade, por tratamento

O rodapé do próprio painel registra a composição da amostra de RQ3 por proveniência de dado (`observed`, `agent_delegated_codex_work`, exclusão de registros `SIM-*`), mantendo rastreabilidade de onde cada métrica veio sem precisar abrir os CSVs separadamente.

## Decisões técnicas do script

- Os agregados de RQ1, RQ2 e inovação são lidos diretamente dos resumos já produzidos pela análise correspondente (`rq1_resumo.csv`, `rq2_resumo.csv`, `inovacao_resumo.csv`).
- Cores fixas por tratamento (`IA` / `Manual`) são compartilhadas com os demais gráficos do relatório (`COLORS` importado de `analyze_rq1_rq2.py`), garantindo consistência visual entre a Figura 8 e as Figuras 1–7.

## Rastreabilidade

- Script: `lab02/dashboard/build_dashboard.py`
- Fontes lidas: `lab02/analysis/results/rq1_resumo.csv`, `rq2_resumo.csv`, `inovacao_resumo.csv`, `rq3_detalhe.csv`
- Saída: `reports/figures/dashboard_final.png`
- Uso no relatório final: seção 3.6 (Inovações Propostas pelo Grupo), Figura 8 (seção 4.2) e discussão na seção 4.3.
