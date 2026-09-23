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

| Recorte | Trials | Composição |
|---|---:|---|
| RQ1, RQ2 e inovação | 12 | Fernanda, Vinicius e Islayder, quatro trials cada |
| RQ3 | 12 | Fernanda, Vinicius e Islayder, com quatro artefatos estruturais finais cada |
| Registros `SIM-*` excluídos | 4 | Linhas históricas separadas dos resultados finais de Islayder |
| Incidentes excluídos | 2 | Uma interrupção e um processo residual de Vinicius |

Os quatro ensaios antigos do instrumento de Fernanda foram removidos dos
CSVs, snapshots e resultados de métricas. Os quatro registros atuais passaram
pela validação automática: dois IA, dois Manual, quatro katas únicos, ordem
2 → 1 → 4 → 3, Issues #19, #27, #29 e #28 e status final `green`. Os snapshots
originais não foram versionados; a RQ3 usa artefatos reconstruídos dos códigos
preparatórios existentes e registra essa limitação. O resultado detalhado está em
[`validacao_fernanda.csv`](../../../lab02/analysis/results/validacao_fernanda.csv).

O recorte final de tempo, testes e ciclos contém três participantes completos
e 12 trials. Cada tratamento possui seis observações. Para Islayder, #21 e #25
usam os resultados informados pelo participante; os totais de aceitação foram
conferidos nos arquivos de teste. #24 e #26 preservam os registros do runner.
Todos os 12 trials atingiram `green`. Os katas não têm equivalência de
dificuldade demonstrada.

## 3. RQ1 — Tempo

**Pergunta:** o uso de assistente de IA reduz o tempo para resolver as tarefas?
O desfecho é o tempo do início até `green`, limitado a 2.100 segundos.

| Tratamento | n | Mediana (min) | Q1 | Q3 | IQR | Green | Censurados |
|---|---:|---:|---:|---:|---:|---:|---:|
| IA | 6 | 1,875 | 1,238 | 3,436 | 2,198 | 6 | 0 |
| Manual | 6 | 3,484 | 3,367 | 5,450 | 2,083 | 6 | 0 |

As medianas correspondem a **112,500 s para IA** e **209,010 s para
Manual**, diferença descritiva de **−96,510 s**. Os artefatos gerados antes da
correção não contêm #21 e #25; os valores finais de Islayder estão documentados
no [relatório individual](../lab02_s02/islayder.md).

O Wilcoxon pareado, aplicado às medianas individuais dos dois trials por
tratamento, teve **n = 3 pares, W = 0 e p = 0,25**. Com somente três pares e
katas distintos dentro de cada tratamento, o resultado não oferece evidência
inferencial de diferença. A menor mediana agregada de IA é apenas descritiva.

## 4. RQ2 — Testes

**Pergunta:** o uso de IA reduz falhas nos testes de aceitação?

| Tratamento | n | Green | Passed finais | Failed finais | Mediana da taxa final |
|---|---:|---:|---:|---:|---:|
| IA | 6 | 6 | **54/54** | 0 | 100% |
| Manual | 6 | 6 | **51/51** | 0 | 100% |

Os dois tratamentos terminaram com todos os testes passando. Para Islayder,
#21 contribui com **10/10** e #25 com **9/9**, ambos em um ciclo. No recorte
completo, a mediana da taxa no primeiro ciclo foi 100% para IA e 14,29% para
Manual; no último ciclo, 100% para ambos. Essa diferença inicial mistura
participantes e katas e não demonstra efeito causal.

## 5. Inovação — Evolução durante os trials

Os 12 trials finais somam **18 ciclos**. A mediana foi **1 ciclo em IA** e
**2 ciclos em Manual**; os intervalos foram 1–2 ciclos nos dois tratamentos.
Todos terminaram com 100% dos testes passando. #21 e #25 possuem somente o
ciclo final informado, ambos `green`; nenhuma etapa intermediária foi criada.
Os gráficos foram regenerados com os 12 trials finais e incluem os dois trials
IA de Islayder:

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

O recorte final da RQ3 contém **12 trials**, quatro de cada participante.
Islayder usa os artefatos `RQ3-ISLAYDER-I21`, `RQ3-ISLAYDER-I24`,
`RQ3-ISLAYDER-I25` e `RQ3-ISLAYDER-I26`, todos vinculados a arquivos reais,
medidos pelo coletor e marcados como `source_kind=observed`. Registros
`SIM-S02-*` não entram na seleção final.

Para Fernanda, os quatro caminhos de snapshot originais não foram versionados.
Os artefatos estruturais finais são reconstruções declaradas dos códigos
preparatórios já presentes no repositório; eles passam os testes e reproduzem
as métricas registradas, mas não são apresentados como snapshots do runner.

### Resultados por trial de Islayder

| Kata | Tratamento | LOC | CC média | CC máxima | Duplicação | Linhas duplicadas | Blocos duplicados | Funções |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| K1 — Normalizador de etiquetas | IA | 15 | 4,0 | 4 | 0% | 0 | 0 | 1 |
| K2 — Balanceamento de turnos | Manual | 6 | 4,0 | 4 | 0% | 0 | 0 | 1 |
| K3 — Compactador de sensor | IA | 27 | 2,6667 | 4 | 0% | 0 | 0 | 3 |
| K4 — Manutenção preditiva | Manual | 11 | 3,0 | 3 | 0% | 0 | 0 | 1 |

### Resumo de Islayder

| Métrica | IA: mediana [Q1; Q3], IQR | Manual: mediana [Q1; Q3], IQR |
|---|---:|---:|
| LOC | 21,0 [18,0; 24,0], 6,0 | 8,5 [7,25; 9,75], 2,5 |
| CC média | 3,3334 [3,0000; 3,6667], 0,6667 | 3,5 [3,25; 3,75], 0,5 |
| Duplicação | 0% [0%; 0%], 0% | 0% [0%; 0%], 0% |

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
| LOC | 15,0 [14,25; 15,75], 1,5 | 11,0 [10,25; 12,5], 2,25 |
| CC média | 3,5 [3,0; 4,75], 1,75 | 4,0 [3,25; 4,0], 0,75 |
| Duplicação | 0% [0%; 0%], 0% | 0% [0%; 0%], 0% |

Em Fernanda, os códigos IA tiveram menor mediana de LOC, enquanto a
complexidade mediana e a duplicação foram iguais. No grupo completo, IA teve
maior mediana de LOC (15,0 contra 11,0) e menor mediana de complexidade média
(3,5 contra 4,0). A duplicação foi zero nos 12 artefatos. A amostra é pequena
e mistura katas distintos, portanto a comparação é somente descritiva.

As tabelas e os três gráficos de RQ3 foram regenerados a partir da seleção
final de 12 artefatos. A análise valida que nenhum `trial_id` iniciado por
`SIM-` foi selecionado.

Detalhes e gráficos consolidados da RQ3:

- [`rq3_detalhe.csv`](../../../lab02/analysis/results/rq3_detalhe.csv)
- [`rq3_resumo.csv`](../../../lab02/analysis/results/rq3_resumo.csv)
- [`rq3_loc_ia_vs_manual.png`](../../figures/rq3_loc_ia_vs_manual.png) — strip plot
- [`rq3_complexidade_ia_vs_manual.png`](../../figures/rq3_complexidade_ia_vs_manual.png) — slope chart
- [`rq3_duplicacao_ia_vs_manual.png`](../../figures/rq3_duplicacao_ia_vs_manual.png) — lollipop plot

## 7. Dashboard

**Responsável:** Vinicius  
**Issue:** #35  
**Status:** concluído e validado.

O dashboard é gerado por `python -m lab02.dashboard.build_dashboard`, consome
as tabelas finais de RQ1, RQ2, RQ3 e inovação e grava
[`dashboard_final.png`](../../figures/dashboard_final.png). A validação exige
12 artefatos de RQ3, seis por tratamento, três participantes e ausência de IDs
`SIM-*`.

## 8. Ameaças à validade

- RQ1, RQ2, RQ3 e inovação têm três participantes completos e seis
  observações por tratamento.
- Cada pessoa executou katas diferentes em IA e Manual; a dificuldade dos katas
  pode explicar parte das diferenças.
- Ordem, aprendizado, fadiga e familiaridade com as ferramentas podem afetar os
  tempos e a quantidade de ciclos.
- Quartis calculados com dois trials por tratamento no recorte individual são
  instáveis e servem apenas como descrição.
- A duplicação foi zero nos 12 artefatos válidos da RQ3, portanto não
  discrimina os tratamentos nesse recorte.
- O Wilcoxon com três pares tem poder insuficiente para sustentar inferência.
- Os artefatos IA de Islayder foram produzidos posteriormente para completar a
  RQ3; essa diferença de momento e ambiente deve ser considerada na leitura.

## 9. Conclusões

Nos 12 trials de RQ1 e RQ2, IA apresentou menor mediana agregada de tempo
(112,500 s contra 209,010 s), e os dois tratamentos terminaram com todos os
testes passando: 54/54 em IA e 51/51 em Manual. Na RQ3, com 12 artefatos
estruturais reais, IA teve maior mediana de LOC (15,0 contra 11,0), menor
mediana de complexidade média (3,5 contra 4,0) e a mesma duplicação de 0%.
Os resultados são descritivos e não sustentam afirmação causal sobre
superioridade de um tratamento.

## 10. Situação de fechamento

As análises, tabelas, gráficos, dashboard e artefatos estruturais estão
consolidados. A ausência dos snapshots originais de Fernanda e de evidência
versionada do piloto temporal externo permanece como limitação metodológica,
não como dado faltante a ser inventado.
