# Lab01S02 — Islayder

## O que fiz

Nesta Sprint 2, trabalhei na refatoração da coleta para separar melhor orquestração, paginação, normalização, persistência, checkpoint e validação. Mantive a arquitetura de monólito modular e preparei a coleta paginada para os 1.000 repositórios mais populares do GitHub, usando `stars:>0 sort:stars-desc`.

Implementei e validei a persistência incremental em CSV em `data/raw/repositories_s02.csv`, com checkpoint em JSON para registrar cursor, quantidade persistida, página, arquivo associado e rate limit. A coleta usa `--resume` para continuar a partir do último cursor salvo e evita duplicação de repositórios já persistidos.

## Decisões técnicas

Mantive `PAGE_SIZE=10`, priorizando estabilidade porque páginas grandes já haviam causado erro HTTP 502 com a query completa. Também mantive requisições sequenciais, retry/backoff limitado para erros transitórios e tratamento separado para erros permanentes de autenticação ou GraphQL.

Adicionei monitoramento de rate limit na query com `cost`, `remaining` e `resetAt`. Na coleta real dos 1.000, foram executadas 100 páginas, com custo final informado como 1 por última consulta, `remaining=4882` e `resetAt=2026-08-16T06:24:49Z`.

## Validações e testes

Rodei os testes automatizados com `py -3 -m unittest discover -s tests -v`: 10 testes executados e 10 aprovados. Esses testes cobrem métricas das RQ01-RQ06, paginação, mudança de cursor, limite exato, CSV, checkpoint, resume, retry, erro permanente de GraphQL e validação de registros.

Também executei um teste real pequeno com 10 repositórios. O teste validou autenticação, GraphQL, normalização, persistência CSV e validação básica: 10 registros coletados, 10 únicos, 0 duplicados, 1 página consultada e validação OK.

Na coleta real final, o CSV ficou com 1.000 registros, 1.000 repositórios únicos, 0 duplicados, nenhuma coluna obrigatória ausente, 0 valores negativos inválidos e ordenação decrescente por estrelas confirmada. Foram identificadas 87 linguagens como "Não informado", 43 repositórios com zero issues e 43 casos de RQ06 indefinida por `totalIssues == 0`.

## RQ01 e RQ02

Na análise exploratória inicial da RQ01, a idade mínima foi 2 dias, a mediana foi 2.821 dias e a máxima foi 6.701 dias. Os repositórios mais antigos na amostra final incluem `rails/rails`, `git/git`, `jekyll/jekyll`, `redis/redis` e `jquery/jquery`. Como hipótese preliminar, os repositórios populares tendem a ser maduros, mas existem exceções recentes com muitas estrelas.

Na análise exploratória inicial da RQ02, o mínimo de PRs merged foi 0, a mediana foi 765,5 e o máximo foi 103.110. Os maiores valores apareceram em `firstcontributions/first-contributions`, `llvm/llvm-project`, `elastic/elasticsearch`, `getsentry/sentry` e `home-assistant/core`. Como hipótese preliminar, a distribuição de PRs aceitas é bastante assimétrica, com poucos projetos concentrando volumes muito altos.

## Limitações

Esta ainda não é a análise estatística final da Sprint 3. Os outliers foram apenas identificados para inspeção inicial e não foram removidos automaticamente. Também não interpretei PR merged como garantia de contribuição externa; usei somente a métrica definida pelo laboratório.
