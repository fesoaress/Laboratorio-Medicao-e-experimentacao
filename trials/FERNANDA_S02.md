# S02 — Roteiro de execução de Fernanda

> **Ressalva posterior:** os quatro registros abaixo são ensaios do instrumento
> e não dados experimentais oficiais. O protocolo vigente para a reexecução está
> em `lab02/trials/FERNANDA_REEXECUCAO.md`. Não reutilize os códigos, tempos ou
> Issues desta página como resultados de Fernanda.

Execução concluída em 16/09/2026. Evidências em `reports/sprints/lab02_s02/fernanda.md`.

## Alocação executada

| Ordem | Issue | Kata | Tratamento executado | Trial ID | Status |
|---:|---|---|---|---:|---|
| 1 | `#19` | `kata2_balanceamento_turnos` | IA | `5e85c97fc84f4819a10aa87970316abf` | green |
| 2 | `#27` | `kata1_normalizador_etiquetas` | Manual | `31c7f16ce79c478ab8f81cd8628e6e3c` | green |
| 3 | `#29` | `kata4_manutencao_preditiva` | IA | `bd057b8dcaef41a6a9503c053b9d57f3` | green |
| 4 | `#28` | `kata3_compactador_sensor` | Manual | `4dfbe8c44c964a65ae003d35d6a60754` | green |

Cada Issue é vinculada pelo kata que ela endereça: Kata 1 → `#27`, Kata 2 → `#19`, Kata 3 → `#28`, Kata 4 → `#29`. As Issues `#33`–`#36`, usadas em uma versão anterior destes CSVs, nunca existiram no repositório (a numeração vai até `#32`).

Divergência aberta: os títulos das Issues no GitHub descrevem o tratamento oposto ao executado (ex.: `#27` está intitulada "Kata 1 - IA", mas o kata 1 foi executado como Manual). Os CSVs registram o tratamento efetivamente aplicado, que é o que sustenta o contrabalanceamento frente a Islayder e Vinicius. Os títulos das quatro Issues precisam ser renomeados no GitHub para refletir o tratamento executado.

## Arquivos gerados

- `lab02/trials/results/trials.csv`
- `lab02/trials/results/trial_cycles.csv`
- `lab02/trials/results/solutions/<trial_id>/`
- `lab02/metrics/results/metrics.csv`

## Coleta RQ3 (já executada)

Métricas registradas para os quatro snapshots finais via `run_metrics.py`.

O `run_metrics.py` também grava um JSON detalhado por trial em `lab02/metrics/results/`, mas esses arquivos são ignorados pelo `.gitignore` por serem auditoria local: o CSV consolidado é o artefato versionado. A coluna `json_path` do `metrics.csv` aponta para caminhos que só existem na máquina onde a coleta rodou. Para reproduzi-los em um clone novo, instale `radon` (`pip install -r lab02/metrics/requirements.txt`) e `jscpd` (`npm ci` em `lab02/metrics`) e reexecute `run_metrics.py` para cada snapshot com `--trial-id` e `--issue`.
