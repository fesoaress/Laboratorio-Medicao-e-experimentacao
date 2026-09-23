# Lab02 S02 — Islayder

**COLETA CONCLUÍDA PARA RQ1, RQ2, RQ3 E INOVAÇÃO.** Islayder executou os quatro trials previstos: Katas 1 e 3 com IA e Katas 2 e 4 manualmente. Nos trials IA, foi utilizado o Gemini no celular, e os tempos foram cronometrados durante a execução. Os quatro trials terminaram `green` e possuem artefatos finais rastreáveis para a análise estrutural.

## Ambiente e protocolo

- Participante: Islayder.
- Alocação: Katas 1 e 3 com IA; Katas 2 e 4 com tratamento Manual.
- Assistente nos trials IA: Gemini no celular.
- Time-box previsto no protocolo: 35 minutos por trial.
- Os trials Manual #24 e #26 permanecem vinculados aos registros existentes do runner.
- Para os trials IA #21 e #25, o participante informou tempo, status `green`, um ciclo e aprovação de todos os testes. Os totais foram conferidos diretamente nos arquivos de aceitação: 10 testes no Kata 1 e 9 testes no Kata 3.

## Tabela final dos quatro trials

| Issue | Kata | Tratamento | Tempo observado (s) | Testes | Falhando | Ciclos | Status | LOC | CC média | Duplicação |
|---|---|---|---:|---:|---:|---:|---|---:|---:|---:|
| #21 | `kata1_normalizador_etiquetas` | IA | **75,00** | **10/10** | 0 | **1** | **green** | 15 | 4,0 | 0% |
| #24 | `kata2_balanceamento_turnos` | Manual | **127,17** | **9/9** | 0 | **1** | **green** | 6 | 4,0 | 0% |
| #25 | `kata3_compactador_sensor` | IA | **150,00** | **9/9** | 0 | **1** | **green** | 27 | 2,6667 | 0% |
| #26 | `kata4_manutencao_preditiva` | Manual | **208,02** | **7/7** | 0 | **2** | **green** | 11 | 3,0 | 0% |

## RQ1 — Tempo de execução

**Pergunta:** o uso de assistente de IA reduz o tempo para resolver as tarefas?

O resumo abaixo usa exclusivamente os quatro tempos observados de Islayder. Q1 e Q3 foram calculados por interpolação linear sobre os dois valores de cada tratamento, seguindo a mesma convenção usada pelas análises do projeto.

| Tratamento | n | Tempos (s) | Média (s) | Mediana (s) | Mínimo (s) | Q1 (s) | Q3 (s) | IQR (s) | Máximo (s) | Amplitude (s) |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| IA | 2 | 75,00; 150,00 | 112,500 | 112,500 | 75,00 | 93,750 | 131,250 | 37,500 | 150,00 | 75,00 |
| Manual | 2 | 127,17; 208,02 | 167,595 | 167,595 | 127,17 | 147,383 | 187,808 | 40,425 | 208,02 | 80,85 |

A média e a mediana de IA foram **55,095 s menores** que as de Manual, diferença descritiva de **32,87%** em relação ao tempo Manual. Em minutos, as medianas foram **1,875 min para IA** e **2,793 min para Manual**.

Esse resultado descreve somente os quatro trials de Islayder. Cada tratamento contém dois katas diferentes, sem equivalência de dificuldade demonstrada. Portanto, a diferença não estabelece efeito causal do assistente.

### Teste inferencial

O pareamento adotado pelo projeto para o Wilcoxon é por participante, comparando a mediana individual de IA com a mediana individual de Manual. No recorte individual de Islayder existe apenas **um par**, quantidade insuficiente para inferência. Por isso, o relatório apresenta as estatísticas descritivas e não interpreta um valor-p para este recorte.

## RQ2 — Testes de aceitação

Os totais de aceitação foram conferidos nos arquivos versionados: [`kata1_normalizador_etiquetas/test_solucao.py`](../../../src/katas/kata1_normalizador_etiquetas/test_solucao.py) contém **10** funções `test_*`, e [`kata3_compactador_sensor/test_solucao.py`](../../../src/katas/kata3_compactador_sensor/test_solucao.py) contém **9**. Com o resultado final informado pelo participante, #21 terminou em **10/10** e #25 em **9/9**.

| Tratamento | Trials | Green | Testes finais passando | Testes finais falhando | Taxa final |
|---|---:|---:|---:|---:|---:|
| IA | 2 | 2 | **19/19** | 0 | 100% |
| Manual | 2 | 2 | **16/16** | 0 | 100% |

Os dois tratamentos terminaram com todos os testes de aceitação passando. O percentual de 100% é secundário aos totais absolutos acima.

## Inovação — Evolução por ciclo

Os quatro trials somaram **5 ciclos**. Nos trials IA, #21 e #25 chegaram a `green` no primeiro ciclo. No tratamento Manual, #24 chegou a `green` no primeiro ciclo e #26 no segundo.

| Tratamento | Trials | Ciclos por trial | Mediana de ciclos até green | Mínimo–máximo | Taxa no último ciclo |
|---|---:|---|---:|---:|---:|
| IA | 2 | 1; 1 | **1,0** | 1–1 | 100% |
| Manual | 2 | 1; 2 | **1,5** | 1–2 | 100% |

Como os trials IA possuem somente o ciclo final informado, não foi criada uma evolução intermediária inexistente. Para #26 Manual, o runner registrou 2/7 testes no primeiro ciclo e 7/7 no segundo.

## RQ3 — Qualidade estrutural

Os códigos finais estão listados em [`manifest.csv`](../../../lab02/trials/results/rq3_artifacts/islayder/manifest.csv). As métricas abaixo foram produzidas por `lab02/metrics/run_metrics.py`, usando Radon 6.0.1 e jscpd 5.2.0 sobre cada `solucao.py` real. Nenhuma linha `SIM-S02-*` entra no recorte final.

| Issue | Tratamento | ID estrutural | LOC | CC média | CC máxima | Duplicação | Linhas duplicadas | Blocos duplicados | Funções analisadas |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| #21 | IA | `RQ3-ISLAYDER-I21` | **15** | **4,0** | **4** | **0%** | 0 | 0 | 1 |
| #24 | Manual | `RQ3-ISLAYDER-I24` | **6** | **4,0** | **4** | **0%** | 0 | 0 | 1 |
| #25 | IA | `RQ3-ISLAYDER-I25` | **27** | **2,6667** | **4** | **0%** | 0 | 0 | 3 |
| #26 | Manual | `RQ3-ISLAYDER-I26` | **11** | **3,0** | **3** | **0%** | 0 | 0 | 1 |

### Resumo estrutural de Islayder

| Métrica | IA: mediana [Q1; Q3], IQR | Manual: mediana [Q1; Q3], IQR |
|---|---:|---:|
| LOC | 21,0 [18,0; 24,0], 6,0 | 8,5 [7,25; 9,75], 2,5 |
| CC média | 3,3334 [3,0000; 3,6667], 0,6667 | 3,5 [3,25; 3,75], 0,5 |
| Duplicação | 0% [0%; 0%], 0% | 0% [0%; 0%], 0% |

Nos dois katas IA, a mediana de LOC foi maior que nos dois katas Manual, enquanto a mediana de complexidade média foi ligeiramente menor. A duplicação foi zero nos quatro artefatos. Como cada tratamento usa katas diferentes e há somente duas observações por grupo, os resultados são descritivos.

## Rastreabilidade

- #21 — Kata 1 — IA — Gemini no celular — 75 s — 10/10 testes — 0 falhando — 1 ciclo — `green` — artefato `RQ3-ISLAYDER-I21`.
- #24 — Kata 2 — Manual — `trial_id=0ce8664ce1cc422ca36699dc40e27fc9` — 127,17 s registrados pelo runner.
- #25 — Kata 3 — IA — Gemini no celular — 150 s — 9/9 testes — 0 falhando — 1 ciclo — `green` — artefato `RQ3-ISLAYDER-I25`.
- #26 — Kata 4 — Manual — `trial_id=7a548706e9624806b0c89fa1c4a2b5e5` — 208,02 s registrados pelo runner.

Os registros dos trials Manual foram preservados. Os IDs `RQ3-ISLAYDER-*` identificam somente os artefatos estruturais e não substituem identificadores do runner. Os registros históricos `SIM-S02-*` permanecem fora dos resultados finais.
