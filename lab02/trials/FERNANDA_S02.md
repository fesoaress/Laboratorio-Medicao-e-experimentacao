# S02 — Registro final de Fernanda

Os quatro trials finais foram executados em 20/09/2026, na ordem
contrabalanceada Kata 2 → Kata 1 → Kata 4 → Kata 3.

| Ordem | Issue | Kata | Tratamento | Trial ID | Origem | Status |
|---:|---|---|---|---|---|---|
| 1 | #19 | `kata2_balanceamento_turnos` | IA | `ba0cb83a55764b3389f7da94946c9230` | `agent_delegated_codex_work` | `green` |
| 2 | #27 | `kata1_normalizador_etiquetas` | Manual | `e9bb6d490e1246bd942cc164bb5cd55a` | `observed` | `green` |
| 3 | #29 | `kata4_manutencao_preditiva` | IA | `c33c36f2110a45478c1016a89476035a` | `agent_delegated_codex_work` | `green` |
| 4 | #28 | `kata3_compactador_sensor` | Manual | `077979815f8f417b88718e458c618807` | `observed` | `green` |

## Fontes finais

- Tempos e estados finais: `lab02/trials/results/trials.csv`.
- Evolução por ciclo: `lab02/trials/results/trial_cycles.csv`.
- Validação: `lab02/analysis/results/validacao_fernanda.csv`.
- Artefatos estruturais reconstruídos:
  `lab02/trials/results/rq3_artifacts/fernanda/manifest.csv`.
- Métricas reproduzidas: `lab02/metrics/results/metrics.csv`.

Os quatro trials IA/Manual são resultados finais; os ensaios antigos do
instrumento permanecem documentados apenas como histórico e são excluídos das
análises. Os dois registros `agent_delegated_codex_work` representam execução
delegada documentada, não simulação.

## Limitação de rastreabilidade

Os quatro caminhos `codigo_path` originais não foram versionados. A RQ3 usa
cópias dos códigos preparatórios existentes que passam os testes e reproduzem
as métricas registradas. O manifesto deixa essa reconstrução explícita; esses
arquivos não são chamados de snapshots originais do runner.
