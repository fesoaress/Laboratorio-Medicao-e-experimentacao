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
| `cfr_delivery_s02.csv` (futuro) | CFR de entrega | RQ03(b) |

## Procedimento

    python -m src.s02_dataset

O script:

1. Lê `repositories_final_s02.csv` como espinha dorsal.
2. Faz left join das demais fontes por `full_name`.
3. Renomeia colunas ambíguas para variantes explícitas
   (ex.: `cfr` vira `cfr_ci`).
4. Cria colunas futuras vazias (`cfr_delivery`, `cfr_delivery_source`)
   para permitir merge incremental.
5. Valida duplicatas e cobertura.
6. Escreve `dataset_final_s02.csv` com 311 linhas e 48 colunas.

## Validação

- 311 linhas (uma por repositório elegível).
- Sem duplicatas em `full_name`.
- Todas as fontes cobrem 311 repos; o script reporta ausências.

## Pendências

- `cfr_delivery` só é preenchido depois do consenso (#57) e da rotulagem
  independente dos três avaliadores.
- Análise de sensibilidade é derivada deste dataset, não é uma coluna própria.

## Reprodutibilidade

- Todas as entradas estão em `data/processed/s02/` e são versionadas.
- A janela oficial `[2025-10-01, 2026-10-01)` está em `collection_manifest_s02.json`.
- Nenhuma chamada de API é feita nesta etapa.
