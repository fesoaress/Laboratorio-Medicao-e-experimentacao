## 1. Introdução

As métricas DORA tornaram-se referência para medir desempenho de entrega de software, mas sua origem está majoritariamente em pesquisas com equipes corporativas respondendo a questionários (Forsgren et al., 2018). Pouco se sabe sobre como essas métricas se comportam quando calculadas diretamente dos artefatos técnicos — releases, commits e execuções de CI — de projetos open-source reais.

Este estudo tem como objetivo minerar, a partir da API do GitHub, aproximações (proxies) das quatro métricas DORA clássicas em uma amostra de repositórios públicos populares que usam CI/CD via GitHub Actions, e avaliar o quanto essas aproximações são sensíveis às escolhas de definição operacional feitas pelo grupo.

### Hipóteses informais

**RQ01 (deployment frequency):** esperamos frequência de deploy (releases/semana) concentrada em valores baixos (abaixo de 1/semana) para a maioria dos repositórios, já que releases formais costumam ser menos frequentes que merges ou deploys contínuos em produtos corporativos — a maior parte da amostra deve cair em Medium/Low na classificação DORA de referência.

**RQ02 (lead time for changes):** esperamos que a variante (b) — por commit — produza medianas mais altas e mais variáveis que a variante (a) — por release —, já que um único commit antigo incluído numa release distorce a variante (a) para cima, enquanto a (b) dilui esse efeito entre todos os commits.

**RQ03 (change failure rate):** esperamos CFR(a) (proxy de pipeline) sistematicamente mais alto que CFR(b) (proxy de entrega), porque falhas de CI (lint, testes, builds quebrados) são mais frequentes e mais fáceis de registrar automaticamente do que releases corretivas identificadas por heurística — a maioria dos repositórios deve ficar nas faixas Elite/High de CFR(b) simplesmente por produzir poucas releases corretivas identificáveis.

**RQ04 (tempo de recuperação):** esperamos medianas de recuperação relativamente baixas (horas, não dias) para repositórios populares e ativos, já que esses projetos tendem a ter pipelines de CI estáveis e mantenedores atentos — mas esperamos uma proporção não trivial de episódios censurados, pela própria janela de 12 meses poder terminar no meio de uma falha ainda não corrigida.

**RQ05 (correlação deployment frequency × CFR):** seguindo a literatura DORA, esperamos correlação de Spearman próxima de zero ou levemente negativa (mais deploys associados a *menos* falha, não mais) — contrariando a intuição de que "deployar mais rápido quebra mais", e reforçando a tese DORA de que velocidade e estabilidade não são um trade-off.

**RQ06 (fatores associados a desempenho DORA):** esperamos que popularidade (estrelas) e número de contribuidores estejam associados a melhor desempenho (mais revisão, mais pressão por qualidade), enquanto a diferença por linguagem deve ser pequena ou inconsistente, já que a linguagem em si não determina práticas de CI/CD.

**RQ07 (análise de sensibilidade):** esperamos concordância moderada a substancial (kappa 0,4–0,8) entre as combinações de definição operacional, com a classificação de CFR sendo a mais instável entre as quatro métricas, por depender da heurística de "release corretiva", que é a definição mais indireta e sujeita a erro entre todas.

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
