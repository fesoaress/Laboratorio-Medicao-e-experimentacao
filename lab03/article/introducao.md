# Rascunho de contribuição de Islayder — issue #47

Registrado antes da primeira coleta do Lab03, em 03/10/2026.
As proposições abaixo são hipóteses informais prévias, não resultados.
Este rascunho abrange somente RQ01–RQ03 e depende de revisão do grupo.

O estudo pretende investigar aspectos da entrega de software em repositórios
públicos populares que utilizam GitHub Actions. Releases serão usadas como
proxy de deploy segundo o protocolo do laboratório; a existência de workflows
não comprova, por si só, que haja implantação em produção. A coleta temporal e
o cálculo das métricas permitirão examinar as hipóteses após a definição da
janela oficial de 12 meses e a integração dos componentes do grupo.

## RQ01 — Qual a frequência de deploys dos repositórios populares que usam CI/CD?

**Hipótese prévia H01:** espera-se variação expressiva entre projetos, com
entregas recorrentes em parte da amostra e concentração em ciclos de release
em outros. A automação pode facilitar entregas frequentes, mas popularidade
e uso de Actions não garantem uma frequência alta.

## RQ02 — Qual o tempo entre um commit e seu respectivo deploy?

**Hipótese prévia H02:** espera-se que muitos commits cheguem à entrega em
intervalos relativamente curtos, enquanto uma parcela tenha esperas maiores
por revisão, estabilização ou agrupamento em releases. Essa combinação pode
produzir uma distribuição assimétrica, com alguns tempos muito longos.

## RQ03 — Qual a taxa de falha das mudanças entregues por esses repositórios?

**Hipótese prévia H03:** espera-se uma proporção de falhas menor que a de
entregas bem-sucedidas, com diferenças entre projetos conforme práticas de
validação e complexidade das mudanças. A interpretação dependerá da proxy
operacional de falha adotada pelo grupo; falha de workflow não equivale
automaticamente a incidente em produção.

As hipóteses RQ04–RQ07 e a introdução consolidada ficam a cargo da revisão e
das contribuições dos demais integrantes. Não são entregas concluídas aqui.
