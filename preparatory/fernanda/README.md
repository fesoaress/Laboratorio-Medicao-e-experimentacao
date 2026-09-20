# Execuções técnicas preparatórias — Fernanda

Esta pasta contém soluções de referência produzidas autonomamente pelo Codex
Work para validar os quatro katas, seus testes e o coletor de métricas. **Não é
uma execução experimental de Fernanda e não pode alimentar os CSVs oficiais.**

Alocação preservada: K2–IA, K1–Manual, K4–IA, K3–Manual. O assistente declarado
no relatório S02 é Claude Sonnet 5, indisponível neste ambiente; o Codex Work foi
usado somente nesta preparação técnica, inclusive para as duas referências de
trials classificados como Manual. Na execução oficial, os trials Manual devem
ser feitos sem assistente, conforme o protocolo experimental.

Os testes copiados em cada pasta são idênticos aos testes de aceitação em
`src/katas/`. As métricas preparatórias ficam em `metrics/` e usam
`source_kind=technical_preparatory`.

## Resultado da validação técnica

| Ordem | Kata | Tratamento | Baseline do stub | Referência final | LOC | CC média | CC máxima | Duplicação |
|---:|---|---|---:|---:|---:|---:|---:|---:|
| 1 | K2 — Balanceamento de turnos | IA | 0/9 | 9/9 | 5 | 3,0 | 3 | 0,0% |
| 2 | K1 — Normalizador de etiquetas | Manual | 0/10 | 10/10 | 13 | 4,0 | 4 | 0,0% |
| 3 | K4 — Manutenção preditiva | IA | 0/7 | 7/7 | 14 | 5,0 | 5 | 0,0% |
| 4 | K3 — Compactador de sensor | Manual | 0/9 | 9/9 | 13 | 4,0 | 5 | 0,0% |

Os valores acima são somente evidência de que testes e ferramentas funcionam.
Não há tempo, ciclos humanos, `trial_id` ou Issue experimental associados.
O CSV detalhado está em `metrics/metrics.csv`.
