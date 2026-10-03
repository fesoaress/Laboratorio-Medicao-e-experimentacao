# Lab03 — seleção e metadados DORA (Sprint 01, Islayder)

O estudo usa dados públicos do GitHub. A issue #38 seleciona candidatos sem
duplicatas com REST próprio e biblioteca HTTP genérica da biblioteca padrão
(`urllib`), sem PyGithub ou equivalentes. A seleção ainda não é a amostra final.

## Instalação

Python 3.11+; validação local em Python 3.13.15. Execute na raiz do repositório:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lab03/requirements-dev.txt
.\.venv\Scripts\python.exe -m lab03 --help
.\.venv\Scripts\python.exe -m pytest lab03/tests -q
```

O coletor não requer pacotes externos. Configure `GITHUB_TOKEN` exclusivamente
no ambiente do processo, sem inserir seu valor em código, configuração, JSON
ou logs. O cliente não carrega `.env`; esse arquivo e suas variantes estão
ignorados pelo Git. Sem token, consultas públicas têm quota reduzida.

```powershell
.\.venv\Scripts\python.exe -m lab03 --limit 5 --output-dir lab03/data/processed/smoke
.\.venv\Scripts\python.exe -m lab03 --limit 100
```

`lab03/config/s01.json` define `sample_size`, `per_page` e `search_queries`.
CLI sobrescreve limite, consultas e datas. O limite indica candidatos únicos
processados, não 100 repositórios elegíveis para métricas DORA. A seleção usa
`stars:>1000 is:public`, ordenação decrescente de estrelas e segue `Link: next`.
O manifesto registra a consulta, contagem anunciada pela API,
duplicatas e eventual resposta incompleta. Dados reais mudam entre execuções;
o procedimento e os registros preservados permitem rastrear cada coleta.

Cada consulta entrega no máximo 1.000 itens. Para ampliar o universo:

```powershell
.\.venv\Scripts\python.exe -m lab03 --limit 100 --query 'stars:1001..2000' --query 'stars:2001..5000'
```

As fatias são consumidas na ordem fornecida e deduplicadas por ID e nome
completo sem distinção de maiúsculas. Não há amostragem aleatória nem divisão
automática de faixas nesta sprint; a seleção por popularidade introduz viés.

## Janela oficial

As datas não foram localizadas nos arquivos nem nas issues consultadas #38,
#39, #46 e #47. `start_date` e `end_date` ficam `null`. Quando confirmadas pelo
professor, configure ambas no JSON ou use `--start-date` e `--end-date`.
A convenção é 12 meses `[início, fim)`, fim exclusivo (29/02 ajusta para 28/02).
Seleção e metadados independem da janela. Validações temporais dependem dela.

## Cliente e integração

`lab03/src/github_client.py` fornece `Client.get(path, params) -> APIResponse`,
com `data`, `headers` e `status`. A issue #44 poderá substituir esse cliente.
O cliente envia Accept/versão REST, timeout e Authorization se o ambiente tiver
token. Erros são explícitos, sem imprimir corpos ou credenciais. Rate limit
interrompe a coleta, informa remaining/reset/Retry-After e não provoca retries.

Pendências do grupo: #40 releases/tags, #41 commits, #42 Lead Time (Fernanda);
#43 workflow runs, #44 cache/rate limit completo, #45 CFR(a)/recuperação
(Vinicius); #46 integração completa. Esses componentes não são implementados
por esta contribuição. A issue #47 recebe somente hipóteses RQ01–RQ03.

Referências oficiais: [busca REST](https://docs.github.com/en/rest/search/search#search-repositories),
[paginação](https://docs.github.com/en/rest/using-the-rest-api/using-pagination-in-the-rest-api).

## Metadados e funil — issue #39

A execução padrão coleta metadados retornados pela busca, sem uma chamada
redundante ao endpoint do repositório. Por candidato, consulta workflows com
`per_page=1` (somente existência, sem runs) e contributors com
`per_page=1&anon=true`. O número da página `last` é a contagem retornada pela
API, incluindo anônimos; pode refletir cache do GitHub e não pessoas únicas.
Sem Link, usa 0 ou 1 conforme a lista; HTTP 204 significa repositório vazio.
Se só houver `next` sem `last`, registra erro de metadados e não inventa 1.

`repo_age_days` é o número de dias completos entre `created_at` e o instante
UTC da coleta. `created_at` original é preservado, e a branch vem da API.
Linguagem ausente é válida e fica vazia no CSV. Erros HTTP ou de metadados
mantêm a linha do candidato, campos desconhecidos vazios e motivos explícitos.
Rate limit interrompe chamadas e deixa o restante `pending_metadata_collection`.

Saídas UTF-8 em `--output-dir` (padrão `lab03/data/processed`):

- `repositories_s01.csv`: identidade, estrelas, linguagem, idade, branch,
  contribuidores, Actions, timestamp, status e motivos.
- `selection_funnel_s01.csv`: `stage,count,discarded,pending,reason`.
- `selection_manifest_s01.json`: parâmetros, janela, consultas, erros e totais.

`candidates` conta candidatos únicos efetivamente selecionados; o universo
anunciado pela busca está em `queries[].total_count` no manifesto e não é
somado entre fatias potencialmente sobrepostas. `processed` inclui tentativas
que deram erro; `metadata_complete` conta metadados concluídos. A coluna
`pending` indica quantidades conhecidas aguardando medição. Valores não
medidos em `count`/`discarded` ficam vazios no CSV e aparecem `N/D` no terminal.
As etapas temporais do funil são sequenciais: runs são contabilizados após
aprovação em releases. `final_sample` fica indeterminado enquanto houver
validações ou erros pendentes. `selected` só ocorre com todos os critérios.

Para executar somente #38, acrescente `--candidates-only`; isso produz um JSON
compacto de candidatos e manifesto, sem coleta de contribuidores ou Actions.

Auditoria de campos, UTF-8, duplicatas, idade, URLs e coerência dos totais:

```powershell
.\.venv\Scripts\python.exe -m lab03.src.audit lab03/data/processed/smoke
.\.venv\Scripts\python.exe -m pytest lab03/tests -q --cov=lab03/src --cov-report=term-missing
```

Código de saída: `0` indica coleta solicitada concluída (as validações temporais
podem continuar pendentes); `1` indica erro, candidatos abaixo do limite ou
busca incompleta; `2` indica parâmetros inválidos. CSVs parciais são preservados.
Executar novamente no mesmo diretório substitui os artefatos; use diretórios
distintos para preservar coletas e não misturar smoke com a coleta de 100.

## Contrato para Fernanda/Vinicius

Após coleta temporal pelos responsáveis, use `--validation-csv CAMINHO`.
O CSV deve conter `full_name,start_date,end_date,release_count,valid_workflow_runs`.
Contagens ainda não medidas ficam vazias; `0` é medição real de zero. O coletor
recusa janelas ausentes ou diferentes da configuração oficial e duplicatas.
Os módulos também podem chamar `classify` com `TemporalEvidence` diretamente.
O contrato pressupõe que #40/#43 já filtraram dados na janela oficial e
aplicaram a definição de runs válidos; não coleta nem recalcula esses dados.

Critérios: Actions existente, branch identificada, pelo menos 5 releases e
50 runs válidos na janela. Motivos de descarte incluem `no_github_actions`,
`missing_default_branch`, `insufficient_releases`, `insufficient_workflow_runs`.
Dados ausentes usam `pending_release_validation`/`pending_workflow_validation`;
falhas usam `api_error`/`metadata_error`, sem tratar erro como ausência de Actions.

Os testes usam respostas HTTP mockadas e fixtures pequenas, sem internet ou
token real. Um teste com 100 candidatos simulados verifica o volume solicitado,
sem produzir resultados empíricos. O smoke real e os bloqueadores desta
execução constam em [reports/s01_islayder.md](reports/s01_islayder.md).

Os testes globais com `python -m pytest` encontram colisões anteriores entre
arquivos `test_solucao.py` dos snapshots/katas. Para verificar os módulos de
engenharia sem executar stubs e snapshots de trials:

```powershell
.\.venv\Scripts\python.exe -m pytest lab03/tests lab02/trials/tests lab02/metrics/tests lab02/analysis/tests lab02/dashboard/tests lab02/simulations/islayder_s02/tests -q
```

Esse último comando requer também as dependências existentes em
`requirements.txt` e `lab02/metrics/requirements.txt`.

Referências: [contribuidores REST](https://docs.github.com/en/rest/repos/repos#list-repository-contributors)
e [workflows REST](https://docs.github.com/en/rest/actions/workflows#list-repository-workflows).
