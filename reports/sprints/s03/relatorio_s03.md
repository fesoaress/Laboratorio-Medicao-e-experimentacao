# Sprint 03 — Análise dos resultados do Lab02

## 1. Objetivo da Sprint

Consolidar o experimento IA × Manual para RQ1 (tempo), RQ2 (testes), RQ3
(qualidade estrutural) e a inovação de acompanhar a evolução dos testes ao
longo de cada trial. Este relatório-base registra a análise de Islayder para
RQ1, RQ2 e inovação sobre os dados disponíveis na branch `Laboratorio-2`.
RQ3 e o dashboard permanecem nas seções atribuídas às respectivas pessoas.

## 2. Dados analisados

Fontes: [`trials.csv`](../../../lab02/trials/results/trials.csv),
[`trial_cycles.csv`](../../../lab02/trials/results/trial_cycles.csv),
relatórios S02 de [Islayder](../lab02_s02/islayder.md),
[Fernanda](../lab02_s02/fernanda.md) e
[Vinicius](../lab02_s02/vinicius.md), e regras do
[`README` da instrumentação](../../../lab02/trials/README.md).
Os CSVs brutos têm 14 linhas de trials: 10 `observed` e 4
`observed_simulated`. A auditoria reproduzível está em
[`auditoria_trials.csv`](../../../lab02/analysis/results/auditoria_trials.csv).

| Etapa | Trials | Motivo |
|---|---:|---|
| CSV consolidado | 14 | 3 nomes de participante; 4 katas; 2 tratamentos |
| Simulados excluídos | 4 | Quatro cenários de Islayder sem execução humana, IDs `SIM-*` |
| Observados excluídos | 6 | Duas tentativas inválidas de Vinicius e quatro ensaios do instrumento de Fernanda |
| Analisáveis | 4 | Vinicius: 2 IA e 2 Manual; um trial por kata |

As duas tentativas inválidas de Vinicius incluem um trial `interrupted`
(Issue #1) e um `time-box` de 2.100 s (Issue #22) produzido por um processo
residual; o relatório S02 os descarta. A Issue #22 aparece duas vezes no CSV,
mas só o trial válido entra na análise. Os quatro registros de Fernanda
estão marcados `observed`, porém seu relatório S02 os caracteriza como
ensaio do instrumento: tempos de 0,88–1,84 s e snapshots de referência.
Eles não medem resolução humana sob os tratamentos. Os quatro registros de
Islayder são explicitamente simulados. As Issues, katas e tratamentos de
cada linha analisada batem com a matriz S02; não há `trial_id` nem par
`(trial_id, ciclo)` duplicado e não faltam campos obrigatórios nas linhas
analisadas. Os campos de horário e snapshot vazios nas simulações são
esperados, pois não houve execução observada.

O desenho previa **3 participantes × 4 katas = 12 trials** com dois katas
por tratamento para cada participante. A amostra analisável atual tem apenas
**1 participante e 4 trials**. K1 e K3 foram feitos com IA; K2 e K4,
manualmente. Cada trial tinha limite de 35 minutos. Um `time-box` legítimo
seria mantido como tempo censurado de 2.100 s, e não como green; **não há
time-box válido no conjunto analisável**. O único time-box observado é o
incidente excluído. A equivalência de dificuldade dos katas não foi
demonstrada, conforme [`VALIDACAO.md`](../../../VALIDACAO.md).

## 3. RQ1 — Tempo

**Pergunta:** o uso de assistente de IA reduz o tempo para resolver as
tarefas? O desfecho operacional é o tempo do início até `green`, ou até
2.100 s quando houver censura. Aqui todos os quatro trials incluídos
atingiram `green`; os tempos são, portanto, tempos observados até green.
Mediana, Q1, Q3 e IQR são calculados em minutos, com quartis de interpolação
linear. O [detalhe por participante e kata](../../../lab02/analysis/results/rq1_detalhe.csv)
preserva o identificador do kata.

| Tratamento | n trials | Mediana (min) | Q1 (min) | Q3 (min) | IQR (min) | Green | Censurados |
|---|---:|---:|---:|---:|---:|---:|---:|
| IA | 2 | 3,121 | 1,977 | 4,265 | 2,288 | 2 | 0 |
| Manual | 2 | 6,814 | 6,457 | 7,172 | 0,715 | 2 | 0 |

Em segundos, as medianas são **187,235 s (IA)** e **408,865 s (Manual)**;
a diferença descritiva IA − Manual é **−221,630 s**. Os trials individuais
foram K1 IA 49,95 s, K3 IA 324,52 s, K2 Manual 365,99 s e K4 Manual
451,74 s. Veja o [gráfico de tempo por trial](../../figures/rq1_tempo_ia_vs_manual.png)
e a [tabela calculada](../../../lab02/analysis/results/rq1_resumo.csv).

**Wilcoxon pareado:** não aplicado. O único par possível é o participante
Vinicius, comparando a mediana de seus dois katas IA com a de seus dois
katas Manual. **n efetivo = 1 par; estatística W = não aplicável; valor-p =
não aplicável.** As tarefas dentro do par também são katas diferentes.
O critério e a decisão estão em
[`rq1_wilcoxon.csv`](../../../lab02/analysis/results/rq1_wilcoxon.csv).

A menor mediana observada com IA é apenas uma descrição dos quatro trials
de Vinicius. Não demonstra efeito do assistente: tratamento e kata estão
confundidos dentro do único participante, e a amostra é mínima. Os dois
quartis por grupo são especialmente instáveis. Não há evidência para afirmar
significância estatística nem inferência causal.

## 4. RQ2 — Defeitos e testes

**Pergunta:** o uso de IA reduz defeitos ou melhora o desempenho nos
testes? Os CSVs registram testes de aceitação passando e falhando, total,
taxa de sucesso, status final e ciclos. Não há medida independente de
defeitos em produção; `failed` é falha dos testes do kata. A taxa por trial
evita comparar diretamente números absolutos de testes entre katas com
7–10 casos de aceitação.

| Tratamento | n trials | Green | Time-box | Passed finais / total | Failed finais | Mediana e média da taxa final |
|---|---:|---:|---:|---:|---:|---:|
| IA | 2 | 2 | 0 | 19/19 | 0 | 100% / 100% |
| Manual | 2 | 2 | 0 | 16/16 | 0 | 100% / 100% |

Ambos os tratamentos terminaram com todos os testes passando. A mediana
de falhas finais foi zero em cada tratamento; não existe diferença final
observada nesta amostra. No primeiro ciclo, K1 IA e K3 IA já tinham 100%;
K2 Manual tinha 100% e K4 Manual tinha 0% (0/7). A mediana da taxa do
primeiro ciclo foi 100% para IA e 50% para Manual, mas isso mistura katas
distintos e apenas quatro trials. Não foi aplicado teste inferencial à taxa
final constante em 100%. Fontes:
[resumo calculado](../../../lab02/analysis/results/rq2_resumo.csv),
[detalhe de evolução](../../../lab02/analysis/results/inovacao_detalhe.csv)
e [gráfico dos testes por trial](../../figures/rq2_testes_ia_vs_manual.png).

## 5. Inovação — Evolução durante os trials

A inovação da instrumentação é registrar cada execução de testes, não só o
desfecho final. Os quatro trials analisáveis somam **5 ciclos**: três trials
com **um ciclo** e um com **dois ciclos**. Nos dois trials IA, o green veio no
ciclo 1; no Manual, K2 chegou ao green no ciclo 1 e K4 no ciclo 2. Mediana
dos ciclos até green: **IA 1**, **Manual 1,5**. K4 Manual passou de **0/7
(0%) aos 435,35 s** para **7/7 (100%) aos 451,73 s**. Os demais aparecem
somente como um ponto em 100%, sem trajetória intermediária observada.

Os tempos por ciclo e contagens de passed/failed estão em
[`inovacao_detalhe.csv`](../../../lab02/analysis/results/inovacao_detalhe.csv)
e no CSV bruto de ciclos. Veja a
[evolução percentual ao longo do tempo](../../figures/inovacao_evolucao_testes.png)
e os [ciclos até green](../../figures/inovacao_ciclos_ate_green.png).
O [resumo por tratamento](../../../lab02/analysis/results/inovacao_resumo.csv)
mostra os agregados. O ponto inicial 0% do stub foi verificado na S01, mas
não corresponde a um ciclo medido e não foi inserido artificialmente nos
gráficos. A predominância de trials com um único ciclo limita fortemente a
análise de velocidade de progresso e retrabalho. A diferença observada
entre IA e Manual pode refletir os katas, e não o tratamento.

## 6. RQ3 — Qualidade estrutural

**Responsável:** Fernanda  
**Status:** aguardando consolidação da Issue #34.

### LOC

A preencher por Fernanda com os snapshots elegíveis e a definição de LOC
lógico do coletor (`lab02/metrics/README.md`).

### Complexidade ciclomática

A preencher por Fernanda com média por função/método e distribuição por
tratamento.

### Duplicação

A preencher por Fernanda com percentual e limites do jscpd.

### Análise IA × Manual

A preencher por Fernanda, preservando participante e kata e excluindo
simulações/ensaios inválidos conforme a auditoria de proveniência.

### Interpretação

A preencher por Fernanda com achados, incerteza e limitações da RQ3.

## 7. Dashboard

**Responsável:** Vinicius  
**Issue:** #35  
**Status:** aguardando integração.

Integrar ao dashboard as tabelas e gráficos de RQ1 (tempos e censura), RQ2
(taxa e falhas dos testes), RQ3 (quando consolidada por Fernanda) e inovação
(taxa por ciclo e ciclos até green). Mostrar quantidade de trials,
participantes, katas, `source_kind`, critérios de exclusão e notas de
validade para que o usuário não confunda simulações ou ensaios do
instrumento com dados experimentais.

## 8. Ameaças à validade

- O desenho tem só 3 participantes; **apenas 1 possui dados utilizáveis**
  neste checkout. Quatro trials de uma pessoa não sustentam generalização.
- K1/K3 aparecem somente com IA e K2/K4 somente com Manual no conjunto
  analisável; a dificuldade entre katas não foi demonstrada equivalente.
  O contrabalanceamento planejado se perdeu após excluir a rodada de
  Fernanda e não ter trials reais de Islayder.
- O mesmo participante executou os katas em sequência; aprendizado ou
  fadiga podem afetar tempo e ciclos. A familiaridade prévia com IA pode
  alterar resultados, sem medida suficiente para ajuste.
- O piloto temporal com não participantes não está comprovado nos
  relatórios S02 consultados. Os títulos das Issues dos trials de Fernanda
  ainda divergem do tratamento registrado, segundo seu relatório S02.
- O limite de 35 min censura qualquer trial que não chegue a green. O
  time-box de 2.100 s atualmente no CSV é um incidente documentado,
  não um resultado experimental válido. O script preservará novos
  time-boxes válidos, mas a mediana de duração limitada não será
  interpretada automaticamente como mediana de tempo até green.
- Há somente cinco ciclos válidos e três trials com um ciclo; isso impede
  caracterizar uma curva de aprendizado durante a maioria dos trials.
- O status `observed` sozinho não comprova validade experimental. A
  exclusão documentada da rodada de Fernanda depende da auditoria de
  proveniência no relatório S02, não de manipular os valores para obter
  algum resultado desejado.

## 9. Conclusões

Nos quatro trials analisáveis, a mediana de tempo com IA foi menor, mas
os tratamentos terminaram igualmente com 100% dos testes passando.
A evolução registrada mostra progresso intermediário em apenas um trial
(K4 Manual). Esses resultados descrevem somente Vinicius nos katas e
condições observados; **não permitem afirmar que IA reduziu tempo ou
defeitos no experimento do grupo**. A conclusão global depende da
reexecução válida dos trials pendentes, da RQ3 de Fernanda e da
consolidação final.

## 10. Pendências para fechamento

- **Fernanda — Issue #34:** reexecutar sob protocolo cronometrado os
  quatro trials classificados como ensaio na S02, conferir Issues e
  tratamentos, consolidar LOC, complexidade e duplicação da RQ3 e
  preencher a seção 6 com interpretação.
- **Vinicius — Issue #35:** integrar RQ1, RQ2, RQ3 e inovação ao dashboard,
  com proveniência e limitações visíveis; acrescentar o link e evidências
  de validação à seção 7.
- **Dependência dos dados do grupo:** Islayder ainda não tem quatro
  trials S02 humanos no CSV; só há cenários simulados. A coleta real,
  se retomada pelo grupo, exigirá atualizar os CSVs e reexecutar esta
  análise e o relatório. Confirmar também o piloto temporal pendente.
