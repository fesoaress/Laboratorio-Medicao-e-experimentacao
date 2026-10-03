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
O JSON e manifesto registram a consulta, contagem anunciada pela API,
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
