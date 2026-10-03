# Lab02 S02 — Fernanda

## Ambiente e protocolo

- Participante: Fernanda.
- Ambiente documentado: Python 3.12.10, Windows 10 e Cursor/VS Code.
- Time-box: 35 minutos por trial.
- Ordem contrabalanceada: Kata 2 → Kata 1 → Kata 4 → Kata 3.
- Alocação: Katas 2 e 4 com IA; Katas 1 e 3 manualmente.
- Os trials IA foram registrados com
  `source_kind=agent_delegated_codex_work`; os trials Manual usam
  `source_kind=observed`.

`agent_delegated_codex_work` identifica o modo documentado de execução dos
trials IA e não é uma fixture. Os quatro registros possuem tempo, ciclos,
testes e status no runner e são distintos dos cenários `SIM-*`.

## Resultados finais

| Ordem | Issue | Trial ID | Kata | Tratamento | Tempo (s) | Testes | Ciclos | Status | Origem |
|---:|---|---|---|---|---:|---:|---:|---|---|
| 1 | #19 | `ba0cb83a55764b3389f7da94946c9230` | Kata 2 | IA | 224,89 | 9/9 | 2 | `green` | `agent_delegated_codex_work` |
| 2 | #27 | `e9bb6d490e1246bd942cc164bb5cd55a` | Kata 1 | Manual | 200,00 | 10/10 | 2 | `green` | `observed` |
| 3 | #29 | `c33c36f2110a45478c1016a89476035a` | Kata 4 | IA | 74,02 | 7/7 | 2 | `green` | `agent_delegated_codex_work` |
| 4 | #28 | `077979815f8f417b88718e458c618807` | Kata 3 | Manual | 210,00 | 9/9 | 2 | `green` | `observed` |

Os dois tratamentos terminaram com todos os testes passando. Os tempos
medianos individuais foram 149,455 s em IA e 205,000 s em Manual. Esses valores
descrevem katas diferentes e não isolam um efeito causal do tratamento.

## Evolução por ciclo

| Issue | Tratamento | Ciclo 1 | Ciclo final |
|---|---|---:|---:|
| #19 | IA | 0/9 | 9/9 no ciclo 2 |
| #27 | Manual | 0/10 | 10/10 no ciclo 2 |
| #29 | IA | 0/7 | 7/7 no ciclo 2 |
| #28 | Manual | 0/9 | 9/9 no ciclo 2 |

Todos os trials chegaram a `green` no segundo ciclo. Os ciclos acima vêm de
`lab02/trials/results/trial_cycles.csv`; nenhum ciclo intermediário foi
inferido.

## RQ3 — métricas estruturais

Os caminhos originais registrados pelo runner não foram versionados. Para
preservar a reprodutibilidade, a consolidação criou cópias rastreáveis dos
códigos preparatórios já versionados, que passam os testes e reproduzem as
métricas registradas. Eles estão declarados em
[`manifest.csv`](../../../lab02/trials/results/rq3_artifacts/fernanda/manifest.csv)
e não são apresentados como snapshots originais do runner.

| Issue | Tratamento | LOC | CC média | CC máxima | Duplicação | Linhas duplicadas | Blocos duplicados | Funções |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| #19 | IA | 5 | 3,0 | 3 | 0% | 0 | 0 | 1 |
| #27 | Manual | 13 | 4,0 | 4 | 0% | 0 | 0 | 1 |
| #29 | IA | 14 | 5,0 | 5 | 0% | 0 | 0 | 1 |
| #28 | Manual | 13 | 4,0 | 5 | 0% | 0 | 0 | 2 |

## Rastreabilidade e exclusões

- Os quatro ensaios antigos do instrumento foram excluídos da amostra final
  pela lista documentada em `analyze_rq1_rq2.py`.
- A validação automática confirma quatro katas, duas observações por
  tratamento, Issues únicas, ordem contrabalanceada e status final válido.
- A ausência dos snapshots originais de Fernanda limita a rastreabilidade de
  RQ3, embora os artefatos reconstruídos sejam reais, testáveis e mensuráveis.
