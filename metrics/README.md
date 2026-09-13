# Lab02 — Métricas estruturais (RQ3) — Fernanda

Instrumentação da Sprint 1 para a pergunta:

> **RQ3 — O uso de assistente de IA altera a complexidade ciclomática ou a duplicação do código produzido?**

## Métricas (definição operacional)

| Campo | Definição | Ferramenta |
|---|---|---|
| `loc` | linhas lógicas de código (`lloc`) apenas em `solucao.py` | Radon `raw` |
| `avg_cyclomatic_complexity` | média da CC por função/método | Radon `cc` |
| `duplication_percentage` | % de linhas duplicadas | jscpd |

**Escopo:** somente `solucao.py` do trial.  
**Excluídos:** `test_solucao.py`, `gabarito/`, dependências, caches, código do Lab01.

Testes ficam de fora de propósito: são iguais para todos e não representam código produzido pelo participante.

Para uma solução menor que a janela congelada do jscpd (`minLines=5`, `minTokens=50`), a ferramenta informa zero fontes comparáveis. O coletor registra corretamente `0%` de duplicação; o tamanho continua disponível em `loc`.

Se o código final tiver erro de sintaxe, a linha do trial ainda é preservada: métricas que o Radon não consegue calcular ficam vazias e `analysis_error` registra o motivo. Isso evita excluir silenciosamente os trials não verdes.

## Pré-requisitos

- Python 3.11+ (venv do projeto)
- Node.js + npm (para o jscpd)

```powershell
# Na raiz do repositório
.\.venv\Scripts\pip.exe install -r lab02\metrics\requirements.txt
cd lab02\metrics
npm ci
cd ..\..
```

Versões fixadas:

- Radon `6.0.1` → `lab02/metrics/requirements.txt`
- jscpd `5.2.0` → `lab02/metrics/package.json` + `package-lock.json`
- Config jscpd → `lab02/metrics/.jscpd.json` (`minLines=5`, `minTokens=50`, `mode=mild`)

## Como coletar métricas de um trial

```powershell
.\.venv\Scripts\python.exe lab02\metrics\run_metrics.py <caminho_do_trial> `
  --participant Fernanda `
  --kata kata1 `
  --treatment IA `
  --trial-id <trial_id_de_trials.csv> `
  --issue <numero_da_issue>
```

`<caminho_do_trial>` pode ser a pasta do trial (com `solucao.py`) ou o próprio arquivo `solucao.py`.  
`--treatment` grava os valores canônicos `IA` ou `Manual` (`AI` é aceito apenas como alias de entrada).
Para trials reais, informe também `--trial-id` e `--issue`; o ID passa a ser a chave de *upsert* e mantém repetições rastreáveis. Eles podem ser omitidos somente em exemplos de validação.

### Saídas

1. **JSON detalhado** em `lab02/metrics/results/<participante>_<kata>_<treatment>_<timestamp>.json`
2. **CSV consolidado** em `lab02/metrics/results/metrics.csv` (uma linha por trial; reexecução do mesmo trial faz *upsert*)

Colunas principais do CSV (Pandas):

```text
participant,kata,treatment,loc,avg_cyclomatic_complexity,duplication_percentage
```

## Validação (exemplo didático)

```powershell
.\.venv\Scripts\python.exe lab02\metrics\run_metrics.py lab02\metrics\examples\exemplo_validacao `
  --participant Validacao `
  --kata exemplo_cc `
  --treatment Manual `
  --output-dir lab02\metrics\validation_results
```

Conferência manual da CC no exemplo: média esperada **2.0** (ver comentários em `examples/exemplo_validacao/solucao.py` e `expected.json`).
Essa saída fica separada e ignorada pelo Git, portanto não contamina `results/metrics.csv`.

## Estrutura

```text
lab02/metrics/
  run_metrics.py          # script reproduzível
  requirements.txt        # Radon
  package.json            # jscpd
  package-lock.json
  .jscpd.json             # config fixa de duplicação
  examples/exemplo_validacao/
  results/metrics.csv     # consolidado
```
