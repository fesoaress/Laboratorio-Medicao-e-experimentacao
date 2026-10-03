# Lab01S01 — Islayder

## O que fiz

Minha contribuição até este momento foi a definição da arquitetura inicial do projeto e a organização das pastas e módulos principais. Configurei os arquivos iniciais, como `.gitignore`, `.env.example`, `.env` local e `requirements.txt`, mantendo separadas as responsabilidades de API, coleta, métricas e análise. Também implementei o cliente GraphQL com carregamento local de `GITHUB_TOKEN` via `python-dotenv`, sem registrar token no código ou nos relatórios. Desenvolvi a consulta inicial para os 100 repositórios mais populares e a coleta dos campos necessários para a Sprint 1. Implementei a RQ01 com o cálculo da idade dos repositórios em dias e a RQ02 com a normalização do total de pull requests aceitas. Por fim, executei a consulta real contra a API GraphQL do GitHub e validei uma amostra de 10 repositórios.
