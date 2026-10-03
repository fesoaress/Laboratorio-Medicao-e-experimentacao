# Sprint 01 — contribuição de Islayder (#38, #39 e parte de #47)

Data: 03/10/2026. Branch: `Laboratorio-3`, criada de `main` após
`git pull --ff-only origin main`. Base: `ae58cf2`. O checkout inicial estava
limpo e o remote foi confirmado como `fesoaress/Laboratorio-Medicao-e-experimentacao`.

## Entregas

- #38: busca REST própria de candidatos públicos com estrelas acima de 1.000,
  paginação por Link, limite configurável, limite de 1.000 por consulta,
  fatias configuráveis e deduplicação por ID/nome.
- #39: metadados, contribuidores em uma chamada por candidato, idade em dias,
  branch da API, checagem leve de Actions, CSVs e funil com pendências explícitas.
  Evidências temporais podem ser fornecidas pelo grupo por CSV/interface Python.
- #47: somente hipóteses informais prévias RQ01–RQ03 em `article/introducao.md`.
  O arquivo foi criado às 20:09:11 UTC, antes da coleta de metadados às
  20:17:16 UTC. Não contém resultados ou hipóteses dos colegas.

O cliente usa `urllib`, exclusivamente `GITHUB_TOKEN` do ambiente e não lê
`.env`. Não implementa cache ou estratégia completa de retries/backoff;
rate limit encerra chamadas de forma controlada, preservando registros parciais.

## Coleta real e artefatos

Comando executado com sucesso:

```powershell
.\.venv\Scripts\python.exe -m lab03 --limit 5 --output-dir lab03/data/processed/smoke
```

Instante da coleta: `2026-10-03T20:17:16.570009+00:00` (17:17:16 em São Paulo).
Consulta: `stars:>1000 is:public`, ordenação decrescente por estrelas. A API
anunciou 65.262 correspondências; foram selecionados somente os 5 candidatos
do smoke. Esse total anunciado não é o tamanho da amostra.

| Etapa | Quantidade | Descartes | Pendentes |
|---|---:|---:|---:|
| Candidatos únicos | 5 | 0 | 0 |
| Processados | 5 | 0 | 0 |
| Metadados completos | 5 | 0 | 0 |
| Com Actions | 5 | 0 | 0 |
| Validações temporais pendentes | 5 | 0 | — |
| Pelo menos 5 releases | Não medido | Não medido | 5 |
| Pelo menos 50 runs válidos | Não medido | Não medido | 5 |
| Amostra final | Indeterminada | 0 | 5 |

Zero duplicatas, zero erros HTTP/metadados e nenhum descarte por ausência de
Actions. A linguagem de `sindresorhus/awesome` é ausente na API e permanece
vazia; isso não é erro. Branches `main` e `master` foram lidas da API. As
contagens de contribuidores incluem anônimos e podem refletir cache do GitHub.
O smoke verifica o coletor; estes candidatos não foram declarados elegíveis
para o estudo. Projetos de documentação/listas podem aparecer nessa busca.

Arquivos reais pequenos e versionáveis:

- `lab03/data/processed/smoke/repositories_s01.csv`
- `lab03/data/processed/smoke/selection_funnel_s01.csv`
- `lab03/data/processed/smoke/selection_manifest_s01.json`

## Validação

Ambiente: Python 3.13.15, pytest 9.1.1, pytest-cov 7.1.0, em `.venv` local
ignorada. Coletor compatível com Python 3.11+ e sem dependências externas.
Foram validados instalação por requirements, `--help`, execução do smoke,
auditoria offline e comandos de testes documentados no README.

```powershell
.\.venv\Scripts\python.exe -m pytest lab03/tests lab02/trials/tests lab02/metrics/tests lab02/analysis/tests lab02/dashboard/tests lab02/simulations/islayder_s02/tests -q --cov=lab03/src --cov-report=term-missing
.\.venv\Scripts\python.exe -m lab03.src.audit lab03/data/processed/smoke
.\.venv\Scripts\python.exe -m compileall -q lab03
```

Resultado: **103 testes aprovados** (71 Lab03 + 32 módulos existentes).
Cobertura do código em `lab03/src`: **96%**. Auditoria e compilação passaram.
Os testes cobrem paginação, limite, fatias, duplicatas, campos, idade,
contribuidores, Actions, funil, descarte, erros, interrupção por rate limit e
integração futura de contagens na janela configurada. As respostas HTTP são
mockadas; nenhum teste automatizado exige token ou rede.

Foi validado o processamento de **100 candidatos simulados** em teste offline:
100 processados, 50 com Actions, 50 descartados e 50 pendentes. Esses números
são exclusivamente de uma fixture de teste, não da coleta real. O teste usa
diretório temporário do pytest, sem versionar dados sintéticos como amostra.

O comando global `python -m pytest -q` foi executado e apresentou **23 erros
anteriores de coleta**, por colisões entre arquivos `test_solucao.py` nos
snapshots e katas do Lab02. Os arquivos de treino também incluem stubs por
desenho. Esses arquivos e testes não foram alterados para contornar falhas.
Os 32 testes dos módulos de engenharia do Lab02 passaram separadamente e
na execução integrada acima.

## Bloqueadores e pendências

- `GITHUB_TOKEN` não está disponível no ambiente. A coleta real de 100
  repositórios **não foi executada**; somente o smoke de 5 usou a API real.
  Após configurar a variável, execute `python -m lab03 --limit 100` e audite
  `lab03/data/processed` com o comando documentado.
- Datas oficiais não localizadas nos arquivos nem nas issues consultadas
  #38/#39/#46/#47. `start_date`/`end_date` permanecem `null`, sem datas fictícias.
- Fernanda: #40 releases/tags, #41 commits e #42 Lead Time.
- Vinicius: #43 workflow runs, #44 cache/rate limit completo e #45 CFR(a)/recuperação.
- Grupo: #46 integração completa e revisão de #47/RQ04–RQ07.

## Auditoria de escopo e rastreabilidade

Alterações limitadas a `lab03/`, acréscimos ao README da raiz e regras de
`.gitignore`. Nenhum código ou artefato anterior de Fernanda/Vinicius foi
alterado. Segredos, ambiente virtual, bytecode, cobertura, caches e respostas
cruas ficam ignorados; nenhum token real foi usado nos testes.

Commits são separados por #38, #47 e #39, sem palavras que fechem issues.
As issues permanecem para revisão do grupo. Não há merge em `main` ou PR.
O SHA de cada commit e o estado após push são verificáveis com:

```powershell
git status
git log --oneline --decorate -10
git branch -vv
```

Documentação operacional: [../README.md](../README.md).
Hipóteses: [../article/introducao.md](../article/introducao.md).
