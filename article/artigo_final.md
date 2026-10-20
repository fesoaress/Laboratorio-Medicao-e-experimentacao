# Uma Análise Empírica e de Sensibilidade das Métricas DORA em Repositórios Open-Source via Artefatos do GitHub

**Autores:** [Islayder, Fernanda, Vinicius]  
**Afiliação:** [Laboratório de Medição e Experimentação — 2026]  
**Contato:** [e-mails institucionais]

---

## Resumo

Este estudo investiga a aplicação de aproximações (proxies) das quatro métricas DORA clássicas — *Deployment Frequency* (DF), *Lead Time for Changes* (LT), *Change Failure Rate* (CFR) e *Recovery Time* — em 311 repositórios open-source populares que utilizam GitHub Actions. A partir de dados públicos da API REST/GraphQL do GitHub na janela UTC `[2025-10-01, 2026-10-01)`, avaliamos a sensibilidade das classificações DORA a três definições operacionais (C1: releases estáveis; C2: estáveis + pré-releases; C3: tags ancestrais). Os resultados mostram que a frequência de deploy é predominantemente baixa (82,0% abaixo de 1 release/semana), que o Lead Time por commit (mediana 118,17 h) é menor que por release (179,67 h) e que a definição de falha altera drasticamente a classificação: CFR de CI tem mediana 5,29%, enquanto CFR de entrega (corretivas) tem mediana 22,73%. A análise de sensibilidade revelou concordância apenas moderada a substancial entre definições (Kappa 0,475–0,669), com a dimensão de falha sendo a mais instável (κ=0,0157 entre C1 e C2, com 67,52% de mudanças). Como contribuição original, propomos o uso de *bootstrap* não paramétrico (2.000 reamostragens, seed 42) para estimar a incerteza amostral das medianas e correlações, evidenciando que a associação entre DF e CFR(a) não é distinguível de zero (IC95% `[−0,051; 0,180]`), enquanto DF×CFR(b) permanece estritamente positiva (`[0,578; 0,716]`). O estudo reforça que as métricas DORA, quando aplicadas a código aberto, são altamente dependentes do construto operacional escolhido e que conclusões baseadas apenas em estimativas pontuais são frágeis.

**Palavras-chave:** Métricas DORA; Engenharia de Software Empírica; Open-Source; Análise de Sensibilidade; Bootstrap; GitHub.

---

## 1. Introdução

As métricas DORA tornaram-se referência na indústria para medir o desempenho de entrega de software, mas sua origem está majoritariamente em pesquisas com equipes corporativas respondendo a questionários (Forsgren et al., 2018). Pouco se sabe sobre como essas métricas se comportam quando calculadas diretamente de artefatos técnicos — releases, commits e execuções de CI — de projetos open-source reais. Este estudo minera dados públicos da API do GitHub para calcular proxies das quatro métricas DORA clássicas em uma amostra de 311 repositórios populares que utilizam GitHub Actions, e avalia o quanto essas proxies são sensíveis às escolhas de definição operacional.

### 1.1 Questões de Pesquisa e Hipóteses Informais

As hipóteses abaixo foram registradas antes da coleta (arquivo `introducao.md`, 03/10/2026) e são preservadas sem reescrita retrospectiva:

- **RQ01 (Deployment Frequency):** espera-se frequência concentrada abaixo de 1 release/semana, com a maioria dos repositórios em Medium/Low.
- **RQ02 (Lead Time):** espera-se que a variante por commit (b) produza medianas mais altas que a por release (a), pois um commit antigo incluído em uma release distorce a variante (a) para cima.
- **RQ03 (Change Failure Rate):** espera-se CFR(a) (pipeline/CI) sistematicamente mais alto que CFR(b) (entrega/corretivas), pois falhas de CI são mais frequentes e fáceis de registrar automaticamente.
- **RQ04 (Recovery Time):** espera-se medianas em horas, com proporção não trivial de episódios censurados.
- **RQ05 (DF × CFR):** seguindo a literatura DORA, espera-se correlação de Spearman próxima de zero ou levemente negativa.
- **RQ06 (Fatores):** espera-se que popularidade (estrelas) e número de contribuidores estejam associados a melhor desempenho; diferença por linguagem deve ser pequena ou inconsistente.
- **RQ07 (Sensibilidade):** espera-se concordância moderada a substancial (κ 0,4–0,8) entre definições, com CFR sendo a mais instável.
- **RQ08 (Retrabalho — bônus):** proporção de releases corretivas no ecossistema.

Além das RQs originais, este trabalho introduz uma inovação metodológica: a aplicação de *bootstrap* não paramétrico para estimar intervalos de confiança das medianas e correlações.

---

## 2. Metodologia

### 2.1 Fonte, Janela e População

Dados públicos da API REST e GraphQL do GitHub: metadados, releases, tags, commits e *workflow runs*. Releases são proxies de entrega; a existência de Actions não prova deploy em produção. A janela UTC `[2025-10-01, 2026-10-01)` tem fim exclusivo e foi definida pelo grupo. A unidade estatística é o repositório; medianas da população de repositórios não devem ser confundidas com razões agregadas de todos os eventos. Default branch e SHA observado são preservados para verificar ancestralidade.

**Critérios de inclusão:** repositório público, mais de 1.000 estrelas, uso de GitHub Actions, default branch válida, pelo menos 5 releases estáveis publicadas na janela e 50 *runs* válidos de `push` na default branch. A Tabela 1 resume o funil de seleção.

**Tabela 1 — Funil de seleção da amostra.**

| Etapa | Aprovações | Reprovados nesta etapa | Não medidos |
|---|---:|---:|---:|
| Candidatos únicos | 1.782 | 0 | 0 |
| Públicos | 1.782 | 0 | 0 |
| Default branch identificada | 1.782 | 0 | 0 |
| Actions | 741 | 207 | 834 |
| Releases estáveis publicadas | 493 | 248 | 0 |
| Ancestralidade das releases | 379 | 72 | 42 |
| Runs válidos | 311 | 67 | 1 |
| **Amostra final** | **311** | **1.469 no total** | **2 não resolvidos** |

Fonte: `selection_funnel_s02.csv`. A ordem otimizada evita chamadas após uma reprovação; "não medido" não significa negativo.

Os 311 elegíveis totalizam 27.152 releases estáveis na janela e 494.200 runs observados (454.382 válidos).

### 2.2 Definições Operacionais e Variantes

Para a análise de sensibilidade (RQ07), definimos três combinações operacionais:

**Tabela 2 — Combinações operacionais (C1, C2, C3).**

| Combinação | Entregas para DF | Lead Time | CFR | Recuperação |
|---|---|---|---|---|
| **C1** (Estável) | Releases estáveis | Por release | CFR(a) — runs de CI | CI, comum |
| **C2** (Pré-releases) | Estáveis + pré-releases | Por commit | CFR(b) — corretivas de C2 | CI, comum |
| **C3** (Tags) | Tags ancestrais da default branch | Por commit | CFR(a) — runs de CI | CI, comum |

- **Deployment Frequency (DF):** releases elegíveis por 365 dias, expressas por semana (`n×7/365`) e por mês (`n×30/365`).
- **Lead Time (LT):** commits novos entre releases estáveis formam os intervalos. A variante *por release* usa o commit mais antigo do intervalo; a variante *por commit* usa a mediana de todos os tempos individuais. Por repositório, persistem mediana, Q1, Q3 e IQR com interpolação linear (tipo 7). Durações negativas não são truncadas.
- **CFR(a) — proxy de CI:** `failure/(success+failure)` em runs válidos; conclusões ignoradas ficam fora da razão; denominador zero é ausente.
- **CFR(b) — proxy de entrega:** heurística validada v5 aplicada às releases. Uma release original é considerada falha se houver qualquer release estável estritamente posterior, corretiva, em até 7 dias (política `any_corrective_7d_v1`). Censura incondicional a partir de 2026-09-24. Cada original conta uma vez. A partição é: 20.038 falhas, 6.406 não falhas, 677 censuradas e 31 não calculáveis (denominador global 26.444).
- **Recovery Time:** por workflow, o episódio inicia na primeira falha após um sucesso observado e termina na conclusão do retorno a sucesso. Falhas iniciais sem sucesso anterior não identificam o início do episódio (censura à esquerda). Ausência de recuperação até o fim gera censura à direita; censurados são excluídos da mediana.

### 2.3 Classificação DORA

Seguindo o protocolo do laboratório:

**Tabela 3 — Limiares de classificação DORA.**

| Métrica | Elite (4) | High (3) | Medium (2) | Low (1) |
|---|---|---|---|---|
| DF | ≥7/semana | ≥1/semana e <7 | ≥1/30 dias e <1/semana | <1/30 dias |
| LT (h) | <24 | [24,168) | [168,720) | ≥720 |
| CFR (fração) | ≤0,15 | (0,15;0,30] | (0,30;0,45] | >0,45 |
| Recuperação (h) | <1 | [1,24) | [24,168) | ≥168 |

A categoria geral é o piso da mediana dos quatro escores e exige as quatro métricas. C1 usa DF estável, LT por release, CFR(a) e recuperação.

### 2.4 Análise Estatística

- **RQ05:** `scipy.stats.spearmanr` com p assintótico, teste de permutação bilateral (9.999 permutações, seed 42) e correção de Holm conjunta para os dois testes.
- **RQ06:** Kruskal–Wallis para quatro grupos (quartis globais de estrelas, contribuidores e idade), com ε²=H/(n−1). Família principal de 12 testes (3 fatores × DF, LT release, CFR(a), recuperação), Holm conjunto. Família suplementar de 3 testes para CFR(b), Holm separado.
- **RQ07:** Kappa de Cohen ponderado linearmente (Low<Medium<High<Elite) para concordância entre classificações.
- **Inovação (bootstrap):** 2.000 reamostragens de repositórios (seed 42) para IC percentil 95% das medianas de DF, CFR(a), CFR(b) e dos dois rho da RQ05. Pares preservados nas correlações; réplicas constantes excluídas e contadas.

### 2.5 Validação Interna da Heurística de Corretivas

Amostra-ouro com seed 42: 60 repositórios sorteados e 5 releases reais por repositório (300 itens). Três avaliadores independentes rotularam tipo de projeto, representatividade de entrega e caráter corretivo. Fleiss Kappa: tipo = 0,8629; representatividade = 0,1540; corretiva = 0,7353. Houve 350 unanimidades, 69 maiorias e uma resolução humana (`armbian/build`, reviewer Islayder, decisão `no`).

**Tabela 4 — Validação empírica das versões da heurística.**

| Versão | Precision | Recall | F1 | Resultado |
|---|---:|---:|---:|---|
| v1 | 0,3810 | 0,8727 | 0,5304 | Refinar |
| v2 | 0,4796 | 0,9636 | 0,6405 | Refinar |
| v3 | 0,9057 | 0,4364 | 0,5890 | Refinar |
| v4 | 0,8636 | 0,5182 | 0,6477 | Refinar |
| **v5** | **0,6975** | **0,7545** | **0,7249** | **Aceita** |

v5: TP=83, FP=36, FN=27, TN=154. A inspeção dos erros e as cinco reavaliações na mesma amostra geram otimismo de seleção: trata-se de validação interna, sem teste externo independente.

---

## 3. Resultados

A Tabela 5 sumariza as distribuições principais por repositório.

**Tabela 5 — Distribuições das métricas por repositório.**

| Métrica | Unidade | n | Ausentes | Mediana | Q1 | Q3 | IQR | Mín | Máx |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| DF | releases/semana | 311 | 0 | 0,3260 | 0,1534 | 0,7096 | 0,5562 | 0,0959 | 131,10 |
| LT por release | h | 261 | 50 | 179,667 | 44,895 | 526,770 | 481,874 | 0,0014 | 10.488,39 |
| LT por commit | h | 261 | 50 | 118,170 | 27,719 | 425,645 | 397,926 | 0,0039 | 34.592,49 |
| CFR(a) | fração | 311 | 0 | 0,0529 | 0,0219 | 0,1145 | 0,0925 | 0 | 0,8313 |
| CFR(b) | fração | 311 | 0 | 0,2273 | 0,0833 | 0,4717 | 0,3884 | 0 | 1,0000 |
| Recuperação | h | 286 | 25 | 3,302 | 0,830 | 18,798 | 17,967 | 0,0139 | 2.369,78 |

Fonte: `data/processed/s03/descriptive.csv`. As distribuições estão em `figures/s03/rq01_04_distributions.pdf`, com transformação log(1+x) quando necessário.

**Tabela 6 — Classificação DORA por métrica.**

| Métrica | Low | Medium | High | Elite | Ausentes |
|---|---:|---:|---:|---:|---:|
| DF | 120 | 135 | 49 | 7 | 0 |
| LT release | 50 | 86 | 74 | 51 | 50 |
| LT commit | 44 | 72 | 84 | 61 | 50 |
| CFR(a) | 8 | 13 | 36 | 254 | 0 |
| CFR(b) | 82 | 35 | 83 | 111 | 0 |
| Recuperação | 14 | 40 | 151 | 81 | 25 |
| **Geral C1** | **21** | **93** | **111** | **14** | **72** |

Geral C1: 239 válidos; 72 incompletos não recebem categoria geral.

### RQ01 — Frequência de Deploy

A mediana de DF foi 0,3260 releases/semana (n=311). **255/311 (82,0%)** dos repositórios tiveram menos de uma release por semana, corroborando a hipótese de baixa frequência. A amplitude até 131,10/semana mostra regimes muito distintos de publicação.

### RQ02 — Lead Time

Contrariando a hipótese inicial, a mediana por commit (118,170 h) foi **menor** que a por release (179,667 h). O LT por commit foi menor em 171/261 pares, igual em 5 e maior em 85. A distribuição é assimétrica, com máximos de 10.488,39 h por release e 34.592,49 h por commit. Agrupar commits em releases dilata o tempo máximo de espera, pois a variante por release usa o commit mais antigo do intervalo; a variante por commit pondera implicitamente intervalos com mais commits.

### RQ03 — Taxa de Falha

A hipótese de que CFR(a)>CFR(b) foi **contrariada**. A mediana de CFR(a) foi 5,29%, enquanto CFR(b) foi 22,73%. CFR(b) foi maior em 228/311 pares. As medidas capturam objetos diferentes: CFR(a) observa conclusões de CI; CFR(b) classifica uma release original pela ocorrência de qualquer corretiva posterior em até 7 dias. Os 20.038 originais falhos de 26.444 avaliáveis são um resultado da regra operacional, não uma estimativa de que 75,78% das implantações causaram incidentes. Censuras e dados ausentes não foram imputados como zero.

### RQ04 — Tempo de Recuperação

A mediana foi 3,302 h (n=286), com Q3=18,798 h e máximo de 2.369,78 h. Houve **10.254 episódios**, dos quais apenas **114 (1,11%)** censurados à direita. Os 25 repositórios sem mediana não têm recuperação igual a zero: 23 sem episódios observados e 2 somente com episódios censurados.

### RQ05 — DF está associada a CFR?

**Tabela 7 — Correlações de Spearman (RQ05).**

| Par | n | rho | p assintótico | p permutação | p_Holm | IC95% bootstrap |
|---|---:|---:|---:|---:|---:|---|
| DF × CFR(a) | 311 | 0,0634 | 0,2649 | 0,2639 | 0,2639 | `[−0,051; 0,180]` |
| DF × CFR(b) | 311 | 0,6514 | 6,2×10⁻³⁹ | 0,0001 | 0,0002 | `[0,578; 0,716]` |

A hipótese de associação próxima de zero foi compatível com CFR(a) (rho=0,063, p_Holm=0,264, IC incluindo zero). Para CFR(b), a hipótese foi contrariada por rho=0,651, com IC estritamente positivo. Uma explicação plausível é o acoplamento entre a frequência e a regra temporal de CFR(b): mais eventos em 7 dias oferecem mais oportunidades de observar uma corretiva. Dispersões em `figures/s03/rq05_scatter.pdf`.

### RQ06 — Fatores Associados

**Tabela 8 — Fatores principais (família de 12 testes, Holm conjunto).**

| Fator | Métrica | n | H | p_Holm | ε² |
|---|---|---:|---:|---:|---:|
| Estrelas | DF | 311 | 4,346 | 0,906 | 0,014 |
| Estrelas | LT release | 261 | 4,194 | 0,906 | 0,016 |
| Estrelas | CFR(a) | 311 | 5,403 | 0,723 | 0,017 |
| Estrelas | Recuperação | 286 | 1,141 | 1,000 | 0,004 |
| Contribuidores | DF | 311 | 8,653 | 0,206 | 0,028 |
| Contribuidores | LT release | 261 | 13,053 | **0,045** | 0,050 |
| Contribuidores | CFR(a) | 311 | 0,258 | 1,000 | 0,001 |
| Contribuidores | Recuperação | 286 | 11,979 | 0,060 | 0,042 |
| Idade | DF | 311 | 39,494 | **1,5×10⁻⁷** | 0,127 |
| Idade | LT release | 261 | 43,563 | **2,2×10⁻⁸** | 0,168 |
| Idade | CFR(a) | 311 | 10,514 | 0,103 | 0,034 |
| Idade | Recuperação | 286 | 12,799 | **0,046** | 0,045 |

Estrelas não mostraram efeito significativo após Holm. Contribuidores tiveram efeito fraco em LT (p_Holm=0,045), mas o quartil superior teve mediana 339,18 h contra 126,34 h no inferior — direção descritiva contrária à expectativa. **Idade** foi o fator mais associado a DF e LT. Na família suplementar, idade×CFR(b) teve ε²=0,154, p_Holm=6,8×10⁻¹⁰ (n=311).

### RQ07 — Sensibilidade das Definições

**Tabela 9 — Concordância entre combinações (categoria geral).**

| Comparação | n pareado | Mudanças | % | Kappa linear |
|---|---:|---:|---:|---:|
| C1 × C2 | 233 | 85 | 36,48% | 0,475 |
| C1 × C3 | 213 | 55 | 25,82% | 0,669 |
| C2 × C3 | 210 | 68 | 32,38% | 0,553 |

A maior instabilidade ocorreu em **CFR entre C1 e C2**: 210/311 mudanças (67,52%; κ=0,0157). Entre C1 e C3, DF mudou em 12,22% (κ=0,840) e LT em 47,01% (κ=0,515). LT C2×C3 teve concordância alta (κ=0,932). A análise suplementar na interseção comum de 210 casos manteve o padrão: C1×C2 com 37,62% de mudanças e κ=0,459; C1×C3 com 25,71% e κ=0,673; C2×C3 com 32,38% e κ=0,553. Transições em `figures/s03/rq07_transitions.png`.

### Inovação — Incerteza por Bootstrap

**Tabela 10 — Intervalos de confiança percentil 95% (2.000 reamostragens, seed 42).**

| Estimativa | Valor | Limite inferior | Limite superior |
|---|---:|---:|---:|
| Mediana DF | 0,3260 | 0,2877 | 0,3644 |
| Mediana CFR(a) | 0,0529 | 0,0433 | 0,0611 |
| Mediana CFR(b) | 0,2273 | 0,2000 | 0,2727 |
| rho DF×CFR(a) | 0,0634 | −0,0515 | 0,1797 |
| rho DF×CFR(b) | 0,6514 | 0,5776 | 0,7163 |

Todas as cinco estimativas tiveram 2.000 réplicas válidas. O IC de DF×CFR(a) inclui zero, enquanto DF×CFR(b) permanece estritamente positivo. A figura está em `figures/s03/bootstrap_intervals.pdf`; a tabela, em `data/processed/s03/bootstrap.csv`. Os intervalos quantificam incerteza amostral condicional às definições; não corrigem vieses de seleção nem erro da heurística.

### RQ08 — Retrabalho (Bônus)

O retrabalho foi calculável integralmente em 274 repositórios: mediana **0,4211** (Q1=0,2376; Q3=0,6000; IQR=0,3624). Em 37 repositórios com alguma classificação indisponível, a taxa pontual permaneceu ausente, com limites identificáveis reportados por caso. A razão conta corretivas, não originais seguidos por corretiva, e portanto **não equivale a CFR(b)**. Dados em `data/processed/s03/rework.csv`; gráfico em `figures/s03/rq08_rework.pdf`.

---

## 4. Discussão

### 4.1 Frequência e Lead Time

A hipótese de concentração abaixo de uma release por semana foi corroborada (82,0%; mediana 0,326). A amplitude até 131,10/semana mostra regimes muito distintos; extremos podem refletir automação e organização de versões, não necessariamente maior frequência de implantações em produção.

A expectativa de mediana maior por commit foi contrariada: 118,17 h por commit contra 179,67 h por release. O LT por commit foi menor em 171/261 pares. A própria justificativa original antecipava a influência de commits antigos sobre o máximo por release; esse mecanismo é compatível com a direção observada, embora a direção prevista na hipótese fosse a oposta. A hipótese é mantida como formulada. A assimetria e os extremos apoiam H02, mas os 50 ausentes podem representar históricos mais complexos.

### 4.2 Duas Noções de Falha

A hipótese CFR(a)>CFR(b) foi contrariada: medianas 5,29% e 22,73%, com CFR(b) maior em 228/311 pares. As medidas capturam objetos diferentes. CFR(a) observa conclusões de CI; CFR(b) classifica uma release original pela ocorrência de qualquer corretiva posterior em até 7 dias. Uma mesma corretiva pode demonstrar a condição para vários originais. Publicações frequentes ampliam as oportunidades de satisfazer essa regra mesmo sem evidência de incidente. A diferença entre a razão agregada (75,78%, dominada por projetos com muitas releases) e a mediana de 22,73% reforça a importância do grão estatístico.

A v5 tem 36 falsos positivos e 27 falsos negativos entre 300 casos (precisão 0,697; recall 0,755). As cinco versões foram ajustadas e avaliadas na mesma amostra-ouro: F1=0,725 representa validação interna potencialmente otimista, não validação externa nem prova de que a heurística identifica incidentes.

### 4.3 Recuperação, Correlação e Fatores

A expectativa de medianas em horas foi corroborada (3,30 h), embora Q3=18,80 h e o máximo de 2.369,78 h mostrem heterogeneidade. A censura de 1,11% não inclui falhas já em andamento no início da janela. O resultado caracteriza recuperação do *workflow*, que pode ser distinta da restauração de um serviço em produção.

A hipótese de associação próxima de zero foi compatível com CFR(a) (rho=0,063; IC incluindo zero), mas contrariada para CFR(b) (rho=0,651). O acoplamento entre frequência e a regra temporal de CFR(b) é uma interpretação do desenho, não uma causa demonstrada. Não concluímos que publicar mais provoca defeitos nem que o estudo refuta resultados corporativos DORA, pois o construto e a unidade de observação são diferentes.

Nenhum teste principal de estrelas permaneceu significativo após Holm. Contribuidores tiveram efeito fraco em LT (p_Holm=0,045; ε²=0,050), com direção descritiva contrária à expectativa. Idade apresentou os maiores efeitos para DF (ε²=0,127) e LT (ε²=0,168), além de diferença menor em recuperação (ε²=0,045). Projetos mais antigos podem ter histórias, escopos e processos distintos; o desenho não controla essas explicações concorrentes. A hipótese sobre linguagem não foi testada.

### 4.4 Sensibilidade e Implicações

A expectativa de concordância moderada a substancial foi corroborada (κ 0,475/0,669/0,553). Ainda assim, 25,82%–36,48% dos repositórios pareados mudaram de categoria geral. CFR foi o componente mais instável entre C1 e C2 (67,52% de mudanças; κ=0,0157). A estabilidade geral maior que a desse componente é compatível com a agregação de quatro escores, que pode amortecer alterações de um componente. A coincidência de CFR(a) em C1/C3 e de recuperação nas três combinações decorre de fontes compartilhadas; não é validação independente. Os n pareados gerais diferem (233/213/210), portanto suas diferenças de Kappa não podem ser atribuídas somente às definições; a análise na interseção comum de 210 casos manteve o padrão.

A mediana de retrabalho de 42,11% (274 projetos) descreve o caráter corretivo das publicações; não é a taxa de originais potencialmente falhos. Os achados sustentam uma conclusão centrada em definições: a frequência é predominantemente baixa, o LT depende da unidade de agregação e a relação velocidade–estabilidade depende fortemente da proxy de falha. A inovação explicita a precisão amostral dessas estimativas; a sensibilidade evidencia a fragilidade de comparar categorias sem informar sua operacionalização.

---

## 5. Ameaças à Validade

**Construto.** Releases, pré-releases e tags não equivalem necessariamente a implantações em produção. O Kappa de representatividade de entregas foi apenas 0,154, evidência de dificuldade operacional entre humanos; o consenso posterior não apaga essa baixa concordância. Runs de CI e recuperação de workflows também não medem diretamente incidentes e restauração de serviços. CFR(b) associa temporalmente corretivas a originais e pode classificar vários originais a partir de uma única corretiva. Seu acoplamento com a frequência e o horizonte de 7 dias limita a interpretação de rho=0,651. A classificação DORA usa os limites especificados no laboratório, não uma nova validação desses limites para projetos open-source.

**Interna.** A v5 alcançou F1=0,7249 após cinco avaliações no mesmo consenso, com 36 FP e 27 FN; há risco de otimismo e erro de classificação na população. Sua extensão a pré-releases não dispõe de nova amostra humana independente. Não atribuímos causalidade a correlações ou a diferenças por quartis: idade, complexidade, organização de versões, popularidade e contribuidores podem se confundir. Tags removidas/movidas e referências indisponíveis limitam a reconstrução; SHAs fixos, cache e auditoria preservam evidências sem eliminar essas ameaças.

**Externa.** A seleção favorece repositórios públicos com mais de mil estrelas, Actions, pelo menos cinco releases estáveis e 50 runs válidos na default branch. Há 311 elegíveis após 1.782 candidatos processados; não se trata de amostra aleatória de todo o GitHub nem de equipes corporativas. A ordem da busca e a disponibilidade técnica influenciam a composição. A janela de 12 meses foi definida pelo grupo. Não generalizamos o tipo de projeto rotulado em 60 casos aos demais 251. Dependências e mantenedores compartilhados entre projetos podem reduzir a independência efetiva das observações.

**Conclusão Estatística.** Há 50 LT ausentes na referência e 25 recuperações ausentes; a categoria geral C1 usa somente 239 repositórios. Os n pareados gerais da RQ07 são 233/213/210, afetando a comparabilidade entre coeficientes. Em C2/C3, comparações não ancestrais, 404, erro 422 e durações negativas permanecem explícitos. A exclusão por análise evita zeros artificiais, mas não elimina viés se a falta de dados estiver associada à complexidade. A mediana de recuperação exclui episódios censurados e pode subestimar o tempo de falhas longas; episódios já iniciados antes da janela têm censura à esquerda. Holm controla as famílias declaradas, mas não torna um efeito pequeno relevante nem identifica pares específicos após um Kruskal–Wallis global. Permutação e bootstrap consideram repositórios como unidades independentes, hipótese que pode ser aproximada. ICs percentis com 2.000 réplicas quantificam variação amostral, não os vieses de seleção, erros de proxy ou incerteza de todas as decisões metodológicas.

---

## 6. Conclusão

Este estudo evidenciou que a aplicação das métricas DORA no contexto open-source exige extrema cautela. As métricas não são universais e dependem intrinsecamente da definição operacional (releases estáveis, pré-releases ou tags) e do proxy de falha escolhido (CI vs. entrega corretiva). A introdução do bootstrap e da análise de sensibilidade (RQ07) oferece uma contribuição metodológica robusta, mostrando onde as estimativas são precisas e onde a variabilidade das definições pode confundir a interpretação. A análise bônus de retrabalho (RQ08) revelou mediana de 42,1% de releases corretivas em 274 projetos, indicando alta dependência de correções no ecossistema open-source.

Como trabalhos futuros, recomendamos o desenvolvimento de heurísticas de corretivas com validação externa independente, além de investigar a correlação entre métricas DORA e incidentes reais de produção relatados pelas comunidades open-source.

---

## Referências

FORSGREN, N.; HUMBLE, J.; KIM, G. **Accelerate: The Science of Lean Software and DevOps**. IT Revolution, 2018.

GITHUB. **GitHub REST API Documentation**. Disponível em: https://docs.github.com/en/rest. Acesso em: 10 out. 2026.

SCIPY. **SciPy Reference Guide: Statistical functions**. Disponível em: https://docs.scipy.org. Acesso em: 10 out. 2026.

SCIKIT-LEARN. **Metrics and scoring: Cohen's kappa**. Disponível em: https://scikit-learn.org. Acesso em: 10 out. 2026.

STATSMODELS. **Holm–Bonferroni correction**. Disponível em: https://www.statsmodels.org. Acesso em: 10 out. 2026.