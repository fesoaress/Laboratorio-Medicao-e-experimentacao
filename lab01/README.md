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
- RQ02 — Sistemas populares recebem muitas pull requests aceitas?
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

Execute os comandos deste README a partir de `lab01/` (`cd lab01` na raiz
do repositório). A pasta é a raiz dos dados, relatórios e snapshots do Lab01.
Os imports históricos `src.*` são locais a este laboratório.

Instale as dependências do laboratório:

```text
pip install -r requirements.txt
```

Crie o arquivo local `lab01/.env` (ou `.env` quando estiver em `lab01/`) e
configure a variável `GITHUB_TOKEN` somente nesse ambiente local:

```text
GITHUB_TOKEN=seu_token
```

O arquivo `.env` é local e não deve ser versionado. A árvore histórica não
contém `.env.example`; nenhum modelo ausente foi fabricado na consolidação.

## Coleta da Sprint 2

A coleta principal busca os repositorios mais populares em paginas sequenciais da API GraphQL, sem chamadas concorrentes agressivas. O tamanho padrao da pagina e 10, pois a query completa ja apresentou instabilidade quando enviada com 100 repositorios por requisicao.

Coleta de 100 repositorios:

```text
python src/collection/collect_repositories.py --limit 100 --overwrite
```

Coleta de 1.000 repositorios:

```text
python src/collection/collect_repositories.py --limit 1000 --overwrite
```

Por padrao, o CSV incremental e gravado em:

```text
data/raw/repositories_s02.csv
```

O checkpoint da coleta fica em:

```text
data/raw/repositories_s02.checkpoint.json
```

Se a execucao for interrompida apos paginas ja persistidas, retome com:

```text
python src/collection/collect_repositories.py --limit 1000 --resume
```

A cada pagina, o coletor normaliza os dados, valida os registros, grava o CSV e atualiza o checkpoint com cursor, quantidade persistida, arquivo de saida e informacoes de rate limit. Erros temporarios de rede ou HTTP 502/503/504 usam retry com backoff limitado. Erros permanentes de autenticacao ou GraphQL encerram a coleta de forma controlada.

## Status

Atualizacao Sprint 2: o coletor foi preparado para ate 1.000 repositorios com CSV incremental, checkpoint/resume, retry/backoff, monitoramento de rate limit e validacoes automatizadas. A execucao real da coleta depende da configuracao local de GITHUB_TOKEN.

## Testes e preservação

Na raiz do repositório, usando o ambiente virtual compartilhado de validação:

```powershell
.\.venv\Scripts\python.exe -m pip install -r lab01/requirements.txt -r lab03/requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest lab01/tests -q
```

Também é possível executar `python -m pytest tests -q` dentro de `lab01/`,
com pytest instalado. A configuração global fornece `lab01/` ao caminho de
imports para executar os testes a partir da raiz.

Os 80 arquivos da fonte `Laboratório-1` em `4133fa3c` foram recuperados.
Código, dados, gráficos, DOCX, snapshots e testes permanecem iguais à fonte;
somente este README ganhou o contexto operacional da nova estrutura.
