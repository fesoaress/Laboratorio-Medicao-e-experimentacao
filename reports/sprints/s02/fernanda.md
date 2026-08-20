# Lab01S02 — Fernanda

## O que fiz

Validei RQ03 e RQ04 sobre os 1.000 repositórios coletados por Islayder (`data/raw/repositories_s02.csv`). Para cada métrica, calculei estatísticas descritivas (mínimo, Q1, mediana, Q3, máximo, média e IQR), identifiquei outliers pela regra do IQR (1,5×IQR além de Q1/Q3), analisei casos especiais e formulei hipóteses informais com base nos dados reais. Também atualizei o GitHub Projects com o andamento da Sprint 2 e gerei o snapshot de fechamento em `snapshots/s02_project_snapshot.csv`.

## Decisões técnicas

- **RQ03:** utilizei `release_count` do CSV, derivado de `releases { totalCount }` na query GraphQL. O campo retorna o total de GitHub Releases formais — não inclui tags simples. Repositórios que versionam via tags sem criar Releases formais aparecem com `release_count = 0`, o que é um valor legítimo, não erro de coleta.
- **RQ03 — limitação da API:** a API GraphQL do GitHub retorna no máximo 1.000 releases via `totalCount`. Dos 1.000 repositórios, 21 apresentaram exatamente 1.000 releases — nesses casos, o valor real pode ser superior ao registrado.
- **RQ04:** utilizei `days_since_last_update`, calculado como a diferença em dias inteiros entre a data de coleta (UTC) e `pushedAt`. Escolhi `pushedAt` em vez de `updatedAt` porque queremos medir atualização de código, não mudanças em metadados como descrição ou configurações do repositório.
- **Outliers:** adotei a regra do IQR (1,5×IQR) por ser o método utilizado pelo restante do time (Vinicius em RQ06) e por ser amplamente aceito para dados assimétricos. Os outliers foram identificados e descritos, mas não removidos — a análise estatística final com decisão de remoção fica para a Sprint 3.

## Validações e testes

Confirmei que o CSV contém exatamente 1.000 registros, sem valores ausentes nos campos `release_count`, `pushed_at` e `days_since_last_update`. Nenhum valor negativo foi encontrado em RQ03 ou RQ04. A validação foi feita por leitura direta do CSV e checagem dos campos com scripts Python usando apenas a biblioteca padrão.

## RQ03 — Total de releases

| Indicador | Valor |
|---|---:|
| N | 1.000 |
| Mínimo | 0 |
| Q1 (25%) | 0 |
| Mediana | 39,5 |
| Q3 (75%) | 148,5 |
| Máximo | 1.000 (teto da API) |
| IQR | 148,5 |
| Limite superior IQR | 371,2 |
| Média | 127,29 |
| Outliers (acima do limite) | 92 repos (9,2%) |
| Repos com 0 releases | 280 (28,0%) |
| Repos com 1.000 releases (teto) | 21 (2,1%) |

A distribuição é fortemente assimétrica à direita: 28% dos repositórios têm 0 releases e uma minoria concentra volumes muito altos. A média (127,29) é mais que o triplo da mediana (39,5), confirmando essa assimetria. A mediana é o indicador mais representativo neste caso.

Os 280 repositórios com 0 releases não são erros — são projetos de documentação, curadoria e listas ("awesome") que não adotam o fluxo de GitHub Releases, como `freeCodeCamp/freeCodeCamp`, `sindresorhus/awesome` e `donnemartin/system-design-primer`.

Os 21 repositórios com o teto de 1.000 releases incluem projetos com ciclos de release muito intensos: `langchain-ai/langchain`, `vercel/next.js`, `electron/electron`, `storybookjs/storybook` e `home-assistant/core`.

**Hipótese informal:** sistemas populares não lançam releases com frequência uniforme. Projetos de software ativo concentram altos volumes de releases, enquanto repositórios de documentação e curadoria — que representam parcela relevante do top 1.000 — não utilizam o mecanismo formal de releases do GitHub. A mediana de 39,5 releases sugere frequência moderada entre os projetos que adotam esse fluxo.

## RQ04 — Tempo desde a última atualização

| Indicador | Valor |
|---|---:|
| N | 1.000 |
| Mínimo | 0 dias |
| Q1 (25%) | 1 dia |
| Mediana | 3 dias |
| Q3 (75%) | 52 dias |
| Máximo | 2.448 dias (~6,7 anos) |
| IQR | 51 dias |
| Limite superior IQR | 128,5 dias |
| Média | 114,1 dias |
| Outliers (acima do limite) | 187 repos (18,7%) |
| Repos com 0 dias (push no dia da coleta) | 177 (17,7%) |
| Repos com mais de 365 dias sem push | 114 (11,4%) |

A mediana de 3 dias é o resultado mais expressivo: 60,2% dos repositórios populares tiveram push nos últimos 7 dias. Isso indica que popularidade e atividade recente caminham juntas na maioria dos casos. A média (114,1 dias) é muito superior à mediana pela influência de projetos sem manutenção há anos, que mantêm as estrelas acumuladas no passado.

Os 187 outliers (mais de 128 dias sem push) incluem projetos descontinuados com histórico relevante: `exacity/deeplearningbook-chinese` (2.448 dias, último push em 2019), `atom/atom` (1.321 dias, editor descontinuado pelo GitHub em 2022) e `adobe/brackets` (1.526 dias, editor descontinuado pela Adobe). Esses são valores extremos legítimos — não erros de coleta.

**Hipótese informal:** sistemas populares tendem a ser atualizados com frequência. A mediana de 3 dias indica que a maioria dos repositórios mais estrelados é ativamente mantida. Entretanto, existe uma cauda de projetos que acumularam popularidade no passado e hoje estão sem manutenção — representando cerca de 11,4% da amostra com mais de 1 ano sem push.

## Limitações

Esta ainda não é a análise estatística final da Sprint 3. Os outliers de RQ03 e RQ04 foram identificados e descritos, mas não investigados individualmente nem removidos — essa decisão metodológica será tomada na Sprint 3. O teto de 1.000 releases da API GraphQL afeta 21 repositórios; para esses casos, o valor real de releases é desconhecido. A data de referência do cálculo de RQ04 é a data de coleta (agosto de 2026), portanto os valores de `days_since_last_update` refletem o momento da coleta, não a data de leitura posterior do CSV.
