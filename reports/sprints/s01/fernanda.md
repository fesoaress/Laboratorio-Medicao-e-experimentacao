# Lab01S01 — Fernanda

## O que fiz

Configurei o limite de WIP no GitHub Projects (Doing = 3, Review = 2) para reduzir multitarefa no time de três integrantes. Estendi a consulta GraphQL em `repositories.graphql` com os campos `releases { totalCount }` (RQ03) e `pushedAt` (RQ04), mantendo uma única requisição para todas as métricas da Sprint 1. Implementei em `src/metrics/rq03_rq04.py` as funções `normalize_release_count()` e `calculate_days_since_last_update()`, reutilizando o parser de datas ISO 8601 já criado pelo Islayder em `rq01_rq02.py`. Integrei RQ03 e RQ04 em `collect_repositories.py`, incluindo os campos `release_count`, `pushed_at` e `days_since_last_update` na normalização, validação e amostra de saída. Além disso construi a estrutura para fazer o csv

## Decisões técnicas

- **RQ03:** usei `releases { totalCount }` porque a disciplina define a métrica como o total de releases;
- **RQ04:** escolhi `pushedAt` em vez de `updatedAt`, pois queremos medir atualização de **código** (último push), não alterações genéricas de metadados do repositório.
- **WIP limit:** Doing = 3 (máximo de duas issues em desenvolvimento simultâneo) e Review = 2 (evitar gargalo na revisão).
- **Validação:** amostra de até 10 repositórios via GraphQL (`first: 10`), conforme exigência da Sprint 1 para RQ03/RQ04.
