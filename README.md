# Laboratório 01 — Características de Repositórios Populares

Este projeto investiga características dos 1.000 repositórios com maior número de estrelas no GitHub por meio de mineração de dados utilizando a API GraphQL.

## Integrantes

- Islayder Jackson
- Fernanda Soares
- Vinicius Gomes

## Objetivo

O laboratório busca coletar, analisar e visualizar dados de repositórios populares para responder às questões de pesquisa propostas. A estrutura do projeto foi organizada para separar as etapas de comunicação com a API, coleta, cálculo de métricas, análise e produção de relatórios.

## Questões de Pesquisa

- RQ01 — Sistemas populares são maduros/antigos?
- RQ02 — Sistemas populares recebem muita contribuição externa?
- RQ03 — Sistemas populares lançam releases com frequência?
- RQ04 — Sistemas populares são atualizados com frequência?
- RQ05 — Sistemas populares são escritos nas linguagens mais populares?
- RQ06 — Sistemas populares possuem alto percentual de issues fechadas?
- RQ07 — Bônus: relação entre popularidade da linguagem, contribuição externa, releases e frequência de atualização.

## Tecnologias

- Python
- GitHub GraphQL API
- GitHub Projects

## Estrutura do Projeto

```text
src/
  api/
  collection/
  metrics/
  analysis/

data/
  raw/
  processed/

snapshots/

reports/
  sprints/
  figures/

docs/
```

- `src/api`: comunicação e consultas com a API GraphQL;
- `src/collection`: scripts responsáveis pela coleta;
- `src/metrics`: cálculo das métricas das questões de pesquisa;
- `src/analysis`: análise e visualização dos dados;
- `data/raw`: dados originais;
- `data/processed`: dados tratados;
- `snapshots`: estados históricos do GitHub Projects;
- `reports/sprints`: relatórios individuais das sprints;
- `reports/figures`: gráficos e figuras;
- `docs`: documentação complementar.

## Organização do Desenvolvimento

O trabalho é organizado por Issues no GitHub Projects, com cada tarefa associada a um responsável. Os commits devem referenciar o número da Issue correspondente, e o board utiliza o fluxo Backlog → To Do → Doing → Review → Done.

## Configuração

Instale as dependências do projeto:

```text
pip install -r requirements.txt
```

Crie ou copie o arquivo `.env` a partir do modelo `.env.example` e preencha localmente:

```text
GITHUB_TOKEN=seu_token
```

O arquivo `.env` é local e não deve ser versionado. O arquivo `.env.example` serve apenas como modelo e não deve conter token verdadeiro.

## Status

Sprint atual: Lab01S01 — arquitetura inicial e implementação da coleta para 100 repositórios com métricas dos RQ01 ao RQ06. A execução real da coleta depende da configuração local de GITHUB_TOKEN.
