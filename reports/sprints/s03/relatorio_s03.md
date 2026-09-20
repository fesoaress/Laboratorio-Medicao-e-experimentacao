# Sprint 03 — Análise dos resultados do Lab02

## 1. Objetivo da Sprint

Consolidar o experimento IA × Manual para RQ1 (tempo), RQ2 (testes), RQ3
(qualidade estrutural) e para a inovação de acompanhar a evolução dos testes
ao longo de cada trial. A análise é reproduzível a partir dos CSVs e dos
snapshots finais versionados no projeto.

## 2. Dados analisados

Fontes: [`trials.csv`](../../../lab02/trials/results/trials.csv),
[`trial_cycles.csv`](../../../lab02/trials/results/trial_cycles.csv),
[`metrics.csv`](../../../lab02/metrics/results/metrics.csv) e
[`auditoria_trials.csv`](../../../lab02/analysis/results/auditoria_trials.csv).

| Etapa | Trials | Motivo |
|---|---:|---|
| CSV consolidado | 14 | 3 participantes, 4 katas e 2 tratamentos |
| Simulados excluídos | 4 | Cenários `SIM-*` de Islayder |
| Incidentes excluídos | 2 | Uma interrupção e um processo residual de Vinicius |
| Analisáveis | 8 | Fernanda e Vinicius, quatro trials cada |

Os quatro ensaios antigos do instrumento de Fernanda foram removidos dos
CSVs, snapshots e resultados de métricas. Os quatro registros atuais passaram
pela validação automática: dois IA, dois Manual, quatro katas únicos, ordem
2 → 1 → 4 → 3, Issues #19, #27, #29 e #28, status final `green` e snapshots
presentes. O resultado detalhado está em
[`validacao_fernanda.csv`](../../../lab02/analysis/results/validacao_fernanda.csv).

A amostra analisável contém dois participantes completos e oito trials. Cada
tratamento possui quatro observações. Todos os trials elegíveis atingiram
`green`; não há censura válida em 35 minutos. A amostra continua pequena e os
katas não têm equivalência de dificuldade demonstrada.

## 3. RQ1 — Tempo

**Pergunta:** o uso de assistente de IA reduz o tempo para resolver as tarefas?
O desfecho é o tempo do início até `green`, limitado a 2.100 segundos.

| Tratamento | n | Mediana (min) | Q1 | Q3 | IQR | Green | Censurados |
|---|---:|---:|---:|---:|---:|---:|---:|
| IA | 4 | 2,491 | 1,133 | 4,163 | 3,030 | 4 | 0 |
| Manual | 4 | 3,577 | 1,035 | 6,457 | 5,422 | 4 | 0 |

As medianas correspondem a **149,455 s para IA** e **214,595 s para
Manual**, diferença descritiva de **−65,140 s**. O detalhe por trial está em
[`rq1_detalhe.csv`](../../../lab02/analysis/results/rq1_detalhe.csv) e o gráfico
em [`rq1_tempo_ia_vs_manual.png`](../../figures/rq1_tempo_ia_vs_manual.png).

O Wilcoxon pareado, aplicado às medianas individuais dos dois trials por
tratamento, teve **n = 2 pares, W = 1 e p = 1,0**. Com somente dois pares e
katas distintos dentro de cada tratamento, o resultado não oferece evidência
inferencial de diferença. A menor mediana agregada de IA é apenas descritiva.

## 4. RQ2 — Testes

**Pergunta:** o uso de IA reduz falhas nos testes de aceitação?

| Tratamento | n | Green | Passed finais | Failed finais | Mediana da taxa final |
|---|---:|---:|---:|---:|---:|
| IA | 4 | 4 | 35/35 | 0 | 100% |
| Manual | 4 | 4 | 35/35 | 0 | 100% |

Os dois tratamentos terminaram com todos os testes passando. A mediana da taxa
no primeiro ciclo foi 50% para IA e 0% para Manual; no último ciclo, 100% para
ambos. Essa diferença inicial mistura participantes e katas e não demonstra
efeito causal. Fontes: [`rq2_resumo.csv`](../../../lab02/analysis/results/rq2_resumo.csv)
e [`inovacao_detalhe.csv`](../../../lab02/analysis/results/inovacao_detalhe.csv).

## 5. Inovação — Evolução durante os trials

Os oito trials elegíveis somam **13 ciclos**. A mediana foi **1,5 ciclos em
IA** e **2 ciclos em Manual**; os intervalos observados foram 1–2 ciclos nos
dois tratamentos. Todos terminaram em 100% dos testes. Os gráficos preservam
cada execução intermediária:

- [`inovacao_evolucao_testes.png`](../../figures/inovacao_evolucao_testes.png)
- [`inovacao_ciclos_ate_green.png`](../../figures/inovacao_ciclos_ate_green.png)
- [`inovacao_resumo.csv`](../../../lab02/analysis/results/inovacao_resumo.csv)

## 6. RQ3 — Qualidade estrutural

**Responsável:** Fernanda  
**Status:** concluída e validada.

### Método

O coletor analisa somente `solucao.py`. LOC é o `lloc` do Radon, complexidade
ciclomática é a média por função/método, e duplicação é o percentual de linhas
duplicadas do jscpd. O cruzamento usa `trial_id`, valida participante, kata,
tratamento, Issue, proveniência e caminho do snapshot.

### Resultados por trial de Fernanda

| Kata | Tratamento | LOC | CC média | CC máxima | Duplicação |
|---|---|---:|---:|---:|---:|
| K2 — Balanceamento de turnos | IA | 5 | 3,0 | 3 | 0% |
| K4 — Manutenção preditiva | IA | 14 | 5,0 | 5 | 0% |
| K1 — Normalizador de etiquetas | Manual | 13 | 4,0 | 4 | 0% |
| K3 — Compactador de sensor | Manual | 13 | 4,0 | 5 | 0% |

### Resumo de Fernanda

| Métrica | IA: mediana [Q1; Q3], IQR | Manual: mediana [Q1; Q3], IQR |
|---|---:|---:|
| LOC | 9,5 [7,25; 11,75], 4,5 | 13,0 [13,0; 13,0], 0,0 |
| CC média | 4,0 [3,5; 4,5], 1,0 | 4,0 [4,0; 4,0], 0,0 |
| Duplicação | 0% [0%; 0%], 0% | 0% [0%; 0%], 0% |

### Resumo do grupo analisável

| Métrica | IA: mediana [Q1; Q3], IQR | Manual: mediana [Q1; Q3], IQR |
|---|---:|---:|
| LOC | 14,5 [11,75; 15,25], 3,5 | 12,0 [10,75; 13,0], 2,25 |
| CC média | 4,0 [3,0; 5,25], 2,25 | 4,0 [3,75; 4,0], 0,25 |
| Duplicação | 0% [0%; 0%], 0% | 0% [0%; 0%], 0% |

Em Fernanda, os códigos IA tiveram menor mediana de LOC, enquanto a
complexidade mediana e a duplicação foram iguais. No grupo, IA teve maior
mediana de LOC, a mesma complexidade mediana e a mesma duplicação. A inversão
do resultado de LOC entre o recorte individual e o grupo reforça que diferenças
entre katas e implementações pesam mais do que qualquer conclusão simples por
tratamento nesta amostra.

Detalhes e gráficos:

- [`rq3_detalhe.csv`](../../../lab02/analysis/results/rq3_detalhe.csv)
- [`rq3_resumo.csv`](../../../lab02/analysis/results/rq3_resumo.csv)
- [`rq3_loc_ia_vs_manual.png`](../../figures/rq3_loc_ia_vs_manual.png)
- [`rq3_complexidade_ia_vs_manual.png`](../../figures/rq3_complexidade_ia_vs_manual.png)
- [`rq3_duplicacao_ia_vs_manual.png`](../../figures/rq3_duplicacao_ia_vs_manual.png)

## 7. Dashboard

**Responsável:** Vinicius  
**Issue:** #35  
**Status:** aguardando integração.

O dashboard deve consumir as tabelas geradas pelos scripts de análise e exibir
quantidade de trials, participantes, katas, `source_kind`, critérios de
exclusão, tempos, testes e métricas estruturais.

## 8. Ameaças à validade

- Há somente dois participantes completos e quatro observações por tratamento.
- Cada pessoa executou katas diferentes em IA e Manual; a dificuldade dos katas
  pode explicar parte das diferenças.
- Ordem, aprendizado, fadiga e familiaridade com as ferramentas podem afetar os
  tempos e a quantidade de ciclos.
- Quartis calculados com dois trials por tratamento no recorte individual são
  instáveis e servem apenas como descrição.
- A duplicação foi zero em todos os snapshots, portanto não discrimina os
  tratamentos nesta amostra.
- O Wilcoxon com dois pares tem poder insuficiente para sustentar inferência.
- Os quatro registros de Islayder permanecem simulados e foram excluídos.

## 9. Conclusões

Nos oito trials analisáveis, IA apresentou menor mediana agregada de tempo,
mas os dois tratamentos terminaram com 100% dos testes passando. A RQ3 não
mostrou diferença de complexidade mediana nem duplicação; LOC variou de forma
oposta no recorte de Fernanda e no agregado. Os resultados são descritivos e
não sustentam afirmação causal sobre superioridade de um tratamento.

## 10. Pendências para fechamento

- **Fernanda — Issue #34:** RQ3 concluída; preparar commit com trials, métricas,
  tabelas, gráficos e relatório.
- **Vinicius — Issue #35:** integrar as saídas ao dashboard.
- **Islayder:** substituir os cenários simulados por trials reais caso o grupo
  decida ampliar a amostra antes da entrega final.
