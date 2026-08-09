# Lab01S01 — Vinicius

## O que fiz

Implementei a RQ05 (linguagem primária) e a RQ06 (razão de issues fechadas), integrando os campos `primaryLanguage`, `issues` e `closedIssues` ao `repositories.graphql` e à normalização em `collect_repositories.py`, junto com os campos já existentes de RQ01/RQ02. Validei numa amostra de 5-10 repositórios antes de integrar, e depois rodei a consulta real para os 100 repositórios da Sprint 1 — validação sem erros, com resultados condizentes (ex.: `freeCodeCamp/freeCodeCamp` em TypeScript com 99,20% de issues fechadas).

## Dificuldades/observações

Na RQ06, tratei repositórios sem nenhuma issue como razão indefinida em vez de 0%, já que são casos diferentes (ex.: `awesome-python` não usa Issues). Na RQ05, `primaryLanguage: null` foi normalizado como "Não informado" em vez de descartar o repositório. Também tive dificuldade de ambiente: o `.venv` local ficou com Python 3.9 e 3.14 misturados, fazendo o `python-dotenv` parecer "não instalado" mesmo já instalado — resolvido recriando o venv com o interpretador explícito do Homebrew.