# Lab03 — dados públicos do GitHub e métricas DORA

A branch `Laboratorio-3` organiza o laboratório em `src/`, `tests/`, `config/`,
`data/`, `docs/` e `reports/` na raiz do repositório.

## Instalação e testes

Python 3.12+; execução local em Python 3.13.15:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q --cov=src --cov-report=term-missing
.\.venv\Scripts\python.exe -m src.cli --help
```

Os coletores usam `urllib`, sem PyGithub. Testes usam respostas mockadas;
fixtures sintéticas não são amostra empírica. `pytest.ini` seleciona a suíte `tests/`.

## Janela da S02

O material não trazia datas explícitas. O grupo definiu em 10/10/2026:
`start_date=2025-10-01`, `end_date=2026-10-01` (fim exclusivo), em UTC.
`config/s01.json` registra essa decisão do grupo, sem atribuí-la ao professor.
O projeto valida uma janela de 12 meses `[início, fim)`.

## Coleta real S02

Siga [docs/s02_collection.md](docs/s02_collection.md) para autenticação local,
retomada, paginação, estratégia de busca, funil e enriquecimento de contexto.
O alvo é **pelo menos 300 repositórios elegíveis após todos os filtros**.
O limite de candidatos da CLI histórica S01 não satisfaz esse requisito.

Critérios: público, mais de 1000 estrelas, GitHub Actions, default branch
válida, pelo menos 5 releases publicadas estáveis ancestrais dessa branch
e 50 runs válidos `push` na branch, dentro da janela. Conclusões ignoradas
não contam para o mínimo. `selected` exige todos os critérios comprovados.

`GITHUB_TOKEN` é lido do ambiente. Se estiver no `.env`, carregue-o somente
no processo local conforme o procedimento. `.env` e cache bruto são ignorados
pelo Git. Valores de credenciais não entram em código, manifests ou logs.

Saídas reais: `data/processed/s02/`. Smoke histórico: `data/processed/smoke/`.
Durante a coleta, os arquivos S02 são parciais: consulte `target_met` e
`final_sample` no manifesto antes de iniciar o sorteio.

Os componentes existentes de releases/tags (#40), commits (#41), Lead Time
(#42), runs (#43), cache/rate limit (#44), CFR(a)/recuperação (#45) são reutilizados.
Erros e campos não medidos ficam explícitos; ausência não vira zero.
Datas, notas, SHAs, runs e contexto são fatos da API, sem previsão corretiva
ou decisão humana executada pelos coletores.

## Amostra-ouro e validação humana S02

Veja [docs/s02_validation.md](docs/s02_validation.md) para sortear 60×5 com
seed 42, preencher os três CSVs independentes, validar rótulos e calcular
concordância/consenso posteriormente. `python -m src.s02 --help` lista a CLI.
O sorteio exige >=300 elegíveis auditados. Campos humanos começam vazios;
a #54 está validada e a #57 tem Kappa e consenso completos. A resolução humana
de `armbian/build` está registrada separadamente dos CSVs individuais.
A heurística v5 atingiu F1=0,7249. CFR(b) está calculado nos 311 repositórios,
com política e censuras rastreáveis; consulte o
[relatório atual](reports/lab03_s02_validation.md).

## Pipeline histórico S01

```powershell
.\.venv\Scripts\python.exe -m src.cli --limit 5 --output-dir data/processed/outro-smoke
.\.venv\Scripts\python.exe -m src.cli --limit 100
```

`sample_size`, `per_page` e `search_queries` vêm de `config/s01.json`; opções
da CLI podem sobrescrevê-los. O limite conta candidatos únicos, não elegíveis.
A busca REST usa `stars:>1000 is:public`, ordena por estrelas e segue `Link: next`.
Para consultas além do teto de 1000 resultados, a CLI S01 aceita faixas explícitas;
o coletor S02 faz a subdivisão automaticamente.

Metadados: identidade/URL, estrelas, linguagem, criação, idade em dias completos
UTC, branch, contribuidores e Actions. Contribuidores usam `per_page=1&anon=true`
e o índice `last` da API; não representam pessoas únicas e podem refletir cache
do GitHub. Actions usa `actions/workflows?per_page=1` para verificar existência.

O contrato temporal `full_name,start_date,end_date,release_count,valid_workflow_runs`
é aceito por `--validation-csv` ou por `TemporalEvidence`/`classify` em Python.
Os dados precisam usar a mesma janela configurada. Contagens não medidas são
vazias; erros de API/metadados não representam insuficiência de releases/runs.

O cliente básico `GitHubClient` sinaliza rate limit. `ResilientClient` adiciona
cache, espera por reset/Retry-After e backoff em 5xx. O SHA da default branch
é registrado para verificar ancestralidade; `target_commitish` não é usado
como prova. Commits entre releases são paginados com conferência de completude.
Lead Time negativo e intervalos divergentes preservam evidências e métricas ausentes.

Veja o [dicionário de dados](docs/data_dictionary.md) e o
[relatório histórico S01](reports/s01_islayder.md).

## Sprint 03 — análise reexecutável

```powershell
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'lab03-mpl'
.\.venv\Scripts\python.exe -m src.s03
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing --cov-fail-under=96
```

Consulte [execução, fontes e contratos](docs/s03_analysis.md),
[metodologia S03](article/metodologia_s03.md) e
[processo/participação](reports/s03/process.md). As saídas estatísticas
ficam em `data/processed/s03/`, gráficos em `figures/s03/` e manifests em
`reports/s03/`. A análise offline usa o snapshot complementar da RQ07;
não exige token nem nova seleção. Os dados homologados da S02 são preservados.

Referências: [busca REST](https://docs.github.com/en/rest/search/search#search-repositories),
[paginação](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api),
[contribuidores](https://docs.github.com/en/rest/repos/repos#list-repository-contributors),
[workflows](https://docs.github.com/en/rest/actions/workflows#list-repository-workflows).
