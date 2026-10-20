# Consolidação do dataset final S02 (#51)

## Fonte dos dados

O dataset final (`data/processed/s02/dataset_final_s02.csv`) é o left join de
`repositories_final_s02.csv` com as fontes de métricas abaixo, usando
`full_name` como chave:

| Fonte | Métrica | Variantes |
|---|---|---|
| `deployment_frequency_s02.csv` | Deployment Frequency | RQ01 |
| `lead_time_s01.csv` | Lead Time for Changes | RQ02(a) release, RQ02(b) commit |
| `workflow_metrics_s02.csv` | CFR + Recovery | RQ03(a) CI, RQ04 |
| `cfr_delivery_s02.csv` | CFR de entrega, política de sete dias + heurística validada v5 | RQ03(b) |

## Procedimento

    python -m src.s02_dataset

O script:

1. Lê `repositories_final_s02.csv` como espinha dorsal.
2. Faz left join das demais fontes por `full_name`.
3. Renomeia colunas ambíguas para variantes explícitas
   (ex.: `cfr` vira `cfr_ci`).
4. Incorpora `cfr_delivery` e `cfr_delivery_source` da fonte específica.
   A possibilidade de colunas vazias permanece apenas para execuções parciais.
5. Valida duplicatas e cobertura.
6. Escreve `dataset_final_s02.csv` com 311 linhas e 48 colunas.

## Validação

- 311 linhas (uma por repositório elegível).
- Sem duplicatas em `full_name`.
- Todas as fontes cobrem 311 repos; o script reporta ausências.

## CFR(b) final e sensibilidade

- As três rotulagens estão completas. O consenso inclui uma resolução humana
  documentada de Islayder em `armbian/build`. Heurística v5 aceita: F1=0,724891.
- Os 300 rótulos de validação não podem ser usados diretamente como se
  classificassem todas as releases dos 311 repositórios. CFR(b) exige aplicar
  a política validada a 27.152 releases, com janela de 7 dias, censura final
  incondicional e indisponibilidades explícitas. Todos os 311 CFR(b) estão
  presentes; veja `cfr_delivery_policy.md`.
- Análise de sensibilidade é derivada deste dataset, não é uma coluna própria.

## Auditoria de 20/10/2026

`python -m src.s02_quality` gera `data/validation/dataset_metrics_audit.json`.
O resultado atual tem 311 linhas, zero chaves duplicadas, zero erros nas
fórmulas/tipos/fontes auditadas e status `valid`.
São 311 valores válidos de frequência e CFR(a), 261 de cada variante de lead
time, 286 de recovery e 311 de CFR(b). Fontes duplicadas são rejeitadas
pela consolidação, antes de gravar a saída. O relatório de execução detalha
os motivos dos valores ausentes. Na consolidação final, apenas as duas colunas
de CFR(b) mudaram: as outras 46 foram comparadas com `a8428d2` e preservadas.
A auditoria em si não reescreve o dataset; verifica também os denominadores e
a partição de releases de CFR(b) contra o detalhamento individual.

```powershell
python -m src.corrective_population
python -m src.cfr_delivery
python -m src.s02_dataset
python -m src.s02_quality
```

As duas primeiras etapas recusam destinos existentes para preservar as
execuções. Em uma reprodução limpa, fontes e avaliação versionadas bastam;
para nova execução, use uma pasta de população diferente e uma cópia das
entradas em outro `--folder`. A consolidação pode ser repetida sem coleta.

## Reprodutibilidade

- Todas as entradas estão em `data/processed/s02/` e são versionadas.
- A janela oficial `[2025-10-01, 2026-10-01)` está em `collection_manifest_s02.json`.
- Nenhuma chamada de API é feita nesta etapa.
