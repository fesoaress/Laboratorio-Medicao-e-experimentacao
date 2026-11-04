# Lab04 S01 — cenário P4 e amostra real de CI (#77)

## Pergunta e decisão estatística

Para o workflow de CI **Test** do repositório público
[`fastapi/fastapi`](https://github.com/fastapi/fastapi), a probabilidade de uma
execução concluída falhar ultrapassa 5%?

- **H₀:** p ≤ 0,05; **H₁:** p > 0,05.
- **α = 0,05**, teste unilateral à direita.
- Comparação: teste Z para uma proporção e teste binomial exato, ambos nos
  mesmos dados. Para a hipótese nula composta, os p-valores são calculados
  na fronteira **p₀ = 0,05**.
- A unidade é uma execução de workflow (`run_id`), codificada como
  **sucesso = 0** e **falha = 1**. O denominador contém somente conclusões
  `success` ou `failure`. Canceladas, ignoradas, neutras e execuções sem
  conclusão não contam como sucesso nem como falha.

## Origem e regra de seleção

- Repositório: https://github.com/fastapi/fastapi
- Workflow: [Test (`test.yml`, ID 1929523)](https://github.com/fastapi/fastapi/actions/workflows/test.yml)
- Fonte: [GitHub REST API — workflow runs](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-workflow).
  Consulta paginada: `GET /repos/fastapi/fastapi/actions/workflows/1929523/runs`
  com `branch=master`, `event=push`, `status=completed`,
  `created=2026-07-01..2026-09-30`, `per_page=100` e páginas 1–2.
- Seleção: **todas** as execuções encontradas nesse trimestre civil fechado
  em UTC, do mesmo workflow e branch. Nenhuma execução foi escolhida com
  base em sua conclusão. A primeira incluída foi em
  `2026-07-01T10:20:44Z` e a última em `2026-09-30T14:28:07Z`.
- URLs individuais estão em cada linha de `lab04/data/ci_runs.csv`; por exemplo,
  [primeira execução](https://github.com/fastapi/fastapi/actions/runs/28510561172)
  e [última execução](https://github.com/fastapi/fastapi/actions/runs/36729334923).

A API retornou **177** execuções concluídas pelos filtros: **162 sucessos,
7 falhas e 8 canceladas**. As canceladas foram excluídas, resultando em
**n = 169**, **k = 7** e **p̂ = 7/169 = 0,0414201** (4,14%). São dados
coletados para o Lab04 diretamente do GitHub; nenhum CSV ou resultado do
Lab03 foi reutilizado.

## CSV e reprodução

O CSV contém `run_id, created_at, run_url, repository, workflow_id,
workflow_name, branch, conclusion, failed`. `run_url` aponta para a página
pública da execução. O arquivo está ordenado por data e ID, sem IDs
duplicados. SHA-256 do snapshot:
`C4ED9660804914C2B8653BAC370D9F428B9C5C620467FB7642B67354E56BAB3D`.

Na raiz do repositório, a coleta pode ser refeita com
`python -m lab04.src.collect_ci_runs`. O coletor usa `urllib` da biblioteca
padrão, sem cliente de terceiros da API do GitHub. Para validar e resumir:

```python
from lab04.src.real_data import load_ci_runs, summarize_ci_runs

df = load_ci_runs("lab04/data/ci_runs.csv")
print(summarize_ci_runs(df))  # {'n': 169, 'k': 7, 'p_hat': 7/169}
```

O loader recusa linhas com campos ausentes, IDs repetidos, URL incompatível,
mais de um repositório/workflow/branch, conclusão fora de `success`/`failure`,
data inválida ou indicador binário inconsistente. O dashboard consome esse
loader por meio de `lab04/src/data_adapter.py`.

## Modelo e parâmetros para as simulações

Cada execução pode ser representada por uma variável **Bernoulli(p)**: 1
para falha e 0 para sucesso. Se as execuções fossem independentes e tivessem
a mesma probabilidade p, o total de falhas em n execuções seguiria uma
**Binomial(n, p)**. Para comparar os testes no tamanho observado, usamos
**n = 169**; para erro tipo I sob a fronteira nula, **p = p₀ = 0,05**.
A taxa **p̂ = 0,0414201** descreve esta amostra e pode ser usada como um
cenário empírico exploratório, mas **não substitui p₀**. Para estudar poder
contra H₁, é preciso escolher valores **maiores** que 0,05 (por exemplo,
0,10 como cenário de aumento substantivo), explicitando que não foram
estimados pela amostra.

## Limitações

Esta é uma amostra de um repositório, workflow, branch, evento e período;
não representa todos os projetos nem falhas de produção. Execuções próximas
podem compartilhar commits ou causas de falha, de modo que independência e
p constante são simplificações para as simulações. Uma reexecução do mesmo
`run_id` não é contada como nova observação; o CSV registra a conclusão
exposta pela API no momento da coleta. Consultas futuras podem refletir
reexecuções ou mudanças na disponibilidade dos registros, por isso o CSV
versionado é o snapshot de referência.
