> Registro histórico da primeira análise, anterior à resolução humana e ao CFR(b). O estado atual está em [lab03_s02_validation.md](lab03_s02_validation.md).

# Lab03 S02 — validação e pendência humana

Execução em 20/10/2026, exclusivamente em `Laboratorio-3`, após `git pull
--ff-only origin Laboratorio-3`. HEAD inicial: `a8428d241b92743c30b25ff35d2ffaf2cb70358b`.
Sem push, merge/rebase com `main`, nova coleta ou alteração dos rótulos humanos.

## Resultado atual da #57

Os três avaliadores têm **60/60 repositórios, 300/300 releases e zero erros**,
alinhados aos mesmos IDs e contextos da amostra canônica 60×5. Os SHA-256 foram
calculados antes da análise e reconferidos ao final:

| Avaliador | SHA-256 do CSV individual |
|---|---|
| Islayder | `9cb894ee51a8cfde238dbd3e978064d4ccfc159812f94449b391342419811a51` |
| Fernanda | `f0b3bca6461306a6c3695538a152213b7991215610f200f17c29417625a00cfb` |
| Vinicius | `370fb02756ca4d10141a90857f60600885558fb4a975f6fd976edc3475d8eb9d` |

`python -m src.s02 analyze` calculou Fleiss Kappa sobre os **votos originais,
antes do consenso**, e retornou 2: revisão humana pendente.

| Dimensão | Itens | Kappa | Interpretação do protocolo | Unanimidades | Maiorias 2×1 | Sem maioria |
|---|---:|---:|---|---:|---:|---:|
| `project_type` | 60 | 0,8628963153384747 | Quase perfeita | 52 | 8 | 0 |
| `releases_represent_real_delivery` | 60 | 0,15401301518438168 | Leve | 54 | 5 | 1 |
| `corrective_release` | 300 | 0,7352941176470585 | Substancial | 244 | 56 | 0 |
| Total de decisões distintas | 420 | — | — | 350 | 69 | 1 |

São **70 divergências**, incluindo o empate triplo. A dimensão de entrega
tem 54/60 unanimidades, mas Kappa baixo: Kappa considera a concordância
esperada pelas frequências marginais, não apenas o acordo bruto. A escala
interpretativa é a já implementada no projeto, sem arredondar na categorização.

### Única resolução humana pendente

| Repositório | Dimensão | Release/tag | Islayder | Fernanda | Vinicius |
|---|---|---|---|---|---|
| `armbian/build` | `releases_represent_real_delivery` | Não se aplica: decisão de repositório | `no` | `uncertain` | `yes` |

**Nenhuma categoria final foi escolhida; zero resoluções manuais aplicadas.**
O grupo precisa informar `consensus` (`yes`, `no` ou `uncertain`), `reviewer`
e justificativa em `notes`. Os três campos permanecem vazios no template.
Não se usa IA, heurística ou SemVer para desempate. Unanimidade e maioria
simples resolvem automaticamente os outros 419 casos.

Artefatos: `data/validation/fleiss_kappa.csv`, `analysis_status.json`,
`data/gold_sample/disagreements.csv` (70), `consensus_votes.csv` (420) e
`manual_resolutions_template.csv` (1). **`gold_sample_consensus.csv` não foi
gerado.** Após a decisão, usar `--resolutions` e pastas novas para conservar
esta execução, conforme `docs/s02_validation.md`.

## #58, CFR(b) e gates bloqueados

Sem consenso completo, não foi executada a avaliação empírica de v1/v2.
Não existe versão aceita nem TP/FP/FN/TN, precision, recall ou F1 empíricos
para registrar. Fixtures de testes não são resultados do estudo.

CFR(b): **0 válidos, 311 ausentes**. São pendências de cálculo, não 311
censuras nem zeros. As quantidades censuradas/não calculáveis para CFR(b)
ainda não foram calculadas. Primeiro concluir consenso e avaliação; depois
aplicar a versão válida à população com janela de 7 dias, censura e
proveniência. Os 300 rótulos não classificam todas as releases dos 311 repos.

`python -m src.s02_quality` confirmou 311 repositórios, 48 colunas, zero
duplicatas e zero erros nos tipos/fórmulas/fontes auditados, sem reescrever o
dataset. Os válidos/ausentes estão no relatório de execução e em
`data/validation/dataset_metrics_audit.json`.

## Testes e cobertura

Comando com Python da `.venv`:

```powershell
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=96
```

A execução incluiu `--basetemp` e saída JSON locais ignorados. Resultado:
**486 aprovados, cobertura 97,85%** (3.047/3.114 instruções).
`src/s02_dataset.py`: 97,92%; `src/s02_quality.py`: 99,12%. Piso 96% inalterado.
As 25 novas verificações cobrem joins, variantes, fontes ausentes, duplicatas,
zero, campos grandes, domínios/fórmulas e ausências válidas. A primeira
tentativa local encontrou scikit-learn ausente; foi instalado o
`requirements-dev.txt` já versionado, sem alterar versões.

## Estado inicial e conclusão

O diagnóstico histórico em `data/validation/awaiting_labels/analysis_status.json`
e a importação de Islayder foram preservados; não descrevem a completude atual.
**S02 ainda não está tecnicamente concluída.** A resolução humana acima
impede concluir consenso, validação/seleção da heurística, CFR(b), proveniência
e metodologia final. `article/metodologia_s02.md` distingue o que foi medido
das pendências, preservando os fragmentos autorais.
