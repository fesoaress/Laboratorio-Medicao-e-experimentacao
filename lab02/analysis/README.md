# Lab02 S03 — RQ1, RQ2 e evolução dos testes

As análises de RQ1, RQ2 e inovação leem os resultados instrumentados em
`lab02/trials/results/trials.csv` e `lab02/trials/results/trial_cycles.csv` e
os dois resultados observados fora do runner em
`lab02/trials/results/participant_reported_trials.csv`. Não leem os arquivos de
`lab02/simulations/` nem modifica dados brutos. O script audita também as
linhas simuladas que foram exportadas para os CSVs consolidados e as exclui
dos cálculos. Cada decisão por `trial_id` fica em
[`results/auditoria_trials.csv`](results/auditoria_trials.csv).

## Execução

Na raiz do repositório, com Python 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m lab02.analysis.analyze_rq1_rq2
```

`requirements.txt` contém Pandas e Matplotlib, já usados pelo projeto, e
SciPy para o Wilcoxon pareado quando houver pares válidos. O import de SciPy
ocorre somente se o teste for aplicável. Os gráficos são gerados com o backend
`Agg`, sem interface gráfica.

## Regras de elegibilidade e estatística

- A auditoria verifica esquema, unicidade de `trial_id` e de
  `(trial_id, ciclo)`, Issue, participante, kata, tratamento conforme a matriz
  S02, campos obrigatórios, snapshot, contagens e taxa de testes, sequência
  dos ciclos, timestamps e limite de 35 minutos.
- `observed_simulated` e IDs `SIM-*` ficam fora das análises finais. Trials
  interrompidos/com erro também ficam fora. Exceções documentadas nos
  relatórios S02 são listadas por ID no código e na auditoria. Os quatro trials
  finais de Fernanda são distintos dos ensaios antigos; dois usam `observed` e
  dois usam `agent_delegated_codex_work`, conforme o modo de execução registrado.
- Os trials IA #21 e #25 de Islayder usam
  `participant_reported_observed`: foram cronometrados pelo participante fora do
  runner. A fonte lateral preserva somente os campos informados e não fabrica
  timestamps, snapshots ou ciclos intermediários.
- Um `time-box` válido permanece na análise como duração observada truncada
  em 2.100 s, com indicador de censura; não é chamado de tempo de green.
  Havendo censura, o script não aplica Wilcoxon a esses tempos.
- A mediana e os quartis usam interpolação linear do Pandas. O IQR é
  `Q3 - Q1`. Com apenas dois trials por tratamento, os quartis são
  descritivos e muito instáveis.
- O pareamento previsto para Wilcoxon é por **participante**, comparando a
  mediana dos dois katas IA com a mediana dos dois Manual, somente quando o
  participante concluiu os quatro katas. Ele não é um pareamento do mesmo
  kata dentro da pessoa. Requer pelo menos dois participantes completos e
  nenhum tempo censurado. O teste, quando aplicável, é bicaudal (`scipy.stats.wilcoxon`).
- O resultado final de RQ2 usa proporção de testes passando e contagem de
  falhas por trial. Os totais absolutos de testes variam entre katas (7–10),
  então somas de `passed` não são uma comparação de desempenho isolada.
- Os gráficos de evolução mostram apenas ciclos efetivamente registrados.
  O stub inicial passa 0 testes na validação S01, mas não é um ciclo medido
  durante o trial e não é inserido artificialmente nas curvas.

## Artefatos

Em `results/`: auditoria por trial, resumo e detalhe de RQ1, pares e decisão
do Wilcoxon, resumo de RQ2, resumo e detalhe da inovação. Em
`reports/figures/`: os quatro gráficos `rq1_tempo_ia_vs_manual.png`,
`rq2_testes_ia_vs_manual.png`, `inovacao_evolucao_testes.png` e
`inovacao_ciclos_ate_green.png`.

O texto interpretativo e a proveniência estão em
[`reports/sprints/s03/relatorio_s03.md`](../../reports/sprints/s03/relatorio_s03.md).

## RQ3 e artefatos estruturais finais

O validador abaixo só retorna sucesso quando existem quatro novos trials
oficiais de Fernanda, com dois tratamentos IA, dois Manual, quatro katas, Issues
novas e a ordem contrabalanceada. Os quatro ensaios antigos continuam no CSV
bruto por rastreabilidade, mas são excluídos pela mesma auditoria usada em RQ1
e RQ2.

```powershell
.\.venv\Scripts\python.exe -m lab02.analysis.validate_fernanda_official
.\.venv\Scripts\python.exe -m lab02.analysis.analyze_rq3 --require-fernanda
```

`analyze_rq3.py` cruza `metrics.csv` com os trials finais elegíveis e com os
manifestos de artefatos estruturais de Islayder e Fernanda em
`lab02/trials/results/rq3_artifacts/`. Para cada linha,
o script confere participante, kata, tratamento, Issue, identificador e caminho
do arquivo efetivamente analisado. IDs `SIM-*` e métricas simuladas não são
aceitos na seleção final.

O comando gera `rq3_detalhe.csv`, `rq3_resumo.csv` e os três gráficos
`rq3_*_ia_vs_manual.png`. O resumo contém valores do grupo e por participante,
com mediana, Q1, Q3 e IQR. A execução também falha se algum participante não
tiver os quatro katas finais (dois IA e dois Manual), se faltar arquivo no
manifesto ou se houver divergência entre manifesto e `metrics.csv`.
