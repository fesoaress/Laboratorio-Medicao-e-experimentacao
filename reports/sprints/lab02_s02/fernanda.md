# Lab02 S02 — Fernanda (execução e coleta)

> Preenchido com dados dos CSVs instrumentados (`trials.csv`, `trial_cycles.csv`, `metrics.csv`).

## Ambiente experimental fixado

- Participante: Fernanda
- Linguagem e versão do Python: `Python 3.12.10`
- Sistema operacional: `Windows 10`
- IDE/editor e versão: `Cursor / VS Code`
- Assistente de IA e versão/plano usado nos trials IA: `Claude Sonnet 5`
- Data/período de execução: `16/09/2026, ~21h01 (horário UTC nos CSVs: 2026-09-17T00:01Z)`
- Time-box: 35 minutos por trial

## Alocação e rastreabilidade

Matriz contrabalanceada: tratamento oposto de Islayder/Vinicius em cada kata. Ordem de execução: 2 → 1 → 4 → 3.

| Ordem | Issue | Kata | Tratamento | Tempo (s) | Status | Passando | Falhando | Taxa | Ciclos | Código produzido | Observações |
|---:|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | `#33` | `kata2_balanceamento_turnos` | IA | `0.88` | `green` | `9` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/5e85c97fc84f4819a10aa87970316abf/solucao.py` | Green no 1º ciclo |
| 2 | `#34` | `kata1_normalizador_etiquetas` | Manual | `1.77` | `green` | `10` | `0` | `100.0%` | `2` | `lab02/trials/results/solutions/31c7f16ce79c478ab8f81cd8628e6e3c/solucao.py` | 30% no ciclo 1, green no ciclo 2 |
| 3 | `#35` | `kata4_manutencao_preditiva` | IA | `0.94` | `green` | `7` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/bd057b8dcaef41a6a9503c053b9d57f3/solucao.py` | Green no 1º ciclo |
| 4 | `#36` | `kata3_compactador_sensor` | Manual | `1.84` | `green` | `9` | `0` | `100.0%` | `2` | `lab02/trials/results/solutions/4dfbe8c44c964a65ae003d35d6a60754/solucao.py` | 44,44% no ciclo 1, green no ciclo 2 |

Fonte dos valores: `lab02/trials/results/trials.csv`. Evolução por ciclo em `lab02/trials/results/trial_cycles.csv`. Métricas RQ3 em `lab02/metrics/results/metrics.csv`.

## Registro detalhado por trial

### Trial 1 — Kata 2 — IA

- Issue: `#33`
- Trial ID: `5e85c97fc84f4819a10aa87970316abf`
- Horário de início/fim: `2026-09-17T00:01:24Z` – `2026-09-17T00:01:25Z`
- Tempo e status: `0.88s`, `green`
- Resultado final dos testes: `9/9 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/5e85c97fc84f4819a10aa87970316abf/solucao.py`
- LOC / CC média / duplicação: `4 LOC / CC média 4,0 (máx. 4) / 0,0% duplicação`
- Observações: assistência de IA utilizada.

### Trial 2 — Kata 1 — Manual

- Issue: `#34`
- Trial ID: `31c7f16ce79c478ab8f81cd8628e6e3c`
- Horário de início/fim: `2026-09-17T00:01:25Z` – `2026-09-17T00:01:27Z`
- Tempo e status: `1.77s`, `green`
- Resultado final dos testes: `10/10 passando (100%)`
- Número de ciclos: `2` (ciclo 1: 3/10 = 30%; ciclo 2: 10/10 = 100%)
- Caminho do código: `lab02/trials/results/solutions/31c7f16ce79c478ab8f81cd8628e6e3c/solucao.py`
- LOC / CC média / duplicação: `14 LOC / CC média 6,0 (máx. 6) / 0,0% duplicação`
- Observações: sem assistência de IA.

### Trial 3 — Kata 4 — IA

- Issue: `#35`
- Trial ID: `bd057b8dcaef41a6a9503c053b9d57f3`
- Horário de início/fim: `2026-09-17T00:01:27Z` – `2026-09-17T00:01:28Z`
- Tempo e status: `0.94s`, `green`
- Resultado final dos testes: `7/7 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/bd057b8dcaef41a6a9503c053b9d57f3/solucao.py`
- LOC / CC média / duplicação: `10 LOC / CC média 3,0 (máx. 3) / 0,0% duplicação`
- Observações: assistência de IA utilizada.

### Trial 4 — Kata 3 — Manual

- Issue: `#36`
- Trial ID: `4dfbe8c44c964a65ae003d35d6a60754`
- Horário de início/fim: `2026-09-17T00:01:28Z` – `2026-09-17T00:01:30Z`
- Tempo e status: `1.84s`, `green`
- Resultado final dos testes: `9/9 passando (100%)`
- Número de ciclos: `2` (ciclo 1: 4/9 = 44,44%; ciclo 2: 9/9 = 100%)
- Caminho do código: `lab02/trials/results/solutions/4dfbe8c44c964a65ae003d35d6a60754/solucao.py`
- LOC / CC média / duplicação: `24 LOC / CC média 4,5 (máx. 7) / 0,0% duplicação`
- Observações: sem assistência de IA.

## Evolução dos testes (inovação)

| Trial | Issue | Ciclos | Progressão (% passando) |
|---|---:|---:|---|
| Kata 2 IA | #33 | 1 | 100% |
| Kata 1 Manual | #34 | 2 | 30% → 100% |
| Kata 4 IA | #35 | 1 | 100% |
| Kata 3 Manual | #36 | 2 | 44,44% → 100% |

## Incidentes e desvios do protocolo

- Nenhum trial interrompido ou time-box.
- Nenhum arquivo de gabarito aberto ou copiado para workspace.
- Issues `#33`–`#36` vinculadas aos trials conforme alocação contrabalanceada.

## Checklist antes do commit manual

- [x] A matriz dos três integrantes contrabalança cada kata entre IA e Manual.
- [x] Quatro trials executados por Fernanda (2 IA + 2 Manual).
- [x] Cada linha da tabela confere com `trials.csv`.
- [x] Cada `codigo_path` existe e corresponde ao snapshot final.
- [x] Quatro linhas de RQ3 coletadas em `metrics.csv`.
- [x] Evolução por ciclo registrada em `trial_cycles.csv`.
- [ ] Issues `#33`–`#36` criadas no GitHub Projects com assignee Fernanda (confirmar no Projects).
- [ ] Commits referenciando as Issues publicados.

Procedimento operacional: `lab02/trials/FERNANDA_S02.md`.
