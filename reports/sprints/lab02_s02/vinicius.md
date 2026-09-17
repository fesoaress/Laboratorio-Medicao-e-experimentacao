# Lab02 S02 — Vinicius (execução dos trials)

> Template de coleta. Preenchido somente após executar cada trial real. Nenhum resultado simulado.

## Ambiente experimental fixado

- Participante: Vinicius Gomes
- Linguagem e versão do Python: `Python 3.14.3`
- Sistema operacional: `macOS`
- IDE/editor e versão: `VS Code`
- Assistente de IA e versão/plano usado nos trials IA: `Claude Sonnet 5`
- Data/período de execução: `16/09/2026, entre 20h20 e 21h20 (horário UTC nos CSVs)`
- Time-box: 35 minutos por trial

## Alocação e rastreabilidade

| Ordem | Issue | Kata | Tratamento | Tempo (s) | Status | Passando | Falhando | Taxa | Ciclos | Código produzido | Observações |
|---:|---|---|---|---:|---|---:|---:|---:|---:|---|---|
| 1 | `#22` | `kata1_normalizador_etiquetas` | IA | `49.95` | `green` | `10` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/3e505698c1834835b9610787e16f8e30/solucao.py` | Repetição da mesma Issue após descarte de duas tentativas anteriores (ver Incidentes) |
| 2 | `#30` | `kata2_balanceamento_turnos` | Manual | `365.99` | `green` | `9` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/c1a52ff9328f47e280fbf65650ac5c82/solucao.py` | Sem incidentes |
| 3 | `#31` | `kata3_compactador_sensor` | IA | `324.52` | `green` | `9` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/445ecd175db145fa8e036a732e2bd08d/solucao.py` | Sem incidentes |
| 4 | `#32` | `kata4_manutencao_preditiva` | Manual | `451.74` | `green` | `7` | `0` | `100.0%` | `2` | `lab02/trials/results/solutions/bee52a404549418498f55c6e0e2b2690/solucao.py` | Sem incidentes |

Fonte dos valores: `lab02/trials/results/trials.csv`. A evolução por ciclo fica em `lab02/trials/results/trial_cycles.csv`; as métricas de LOC, complexidade e duplicação ficam em `lab02/metrics/results/metrics.csv`.

## Registro detalhado por trial

### Kata 1 — IA

- Issue: `#22`
- Trial ID: `3e505698c1834835b9610787e16f8e30`
- Horário de início/fim: `2026-09-16T20:41:27Z` – `2026-09-16T20:42:17Z`
- Tempo e status: `49.95s`, `green`
- Resultado final dos testes: `10/10 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/3e505698c1834835b9610787e16f8e30/solucao.py`
- LOC / CC média / duplicação: `15 LOC / CC média 6,0 (máx. 6) / 0,0% duplicação`
- Observações e número de interações com a IA (opcional): `<preencher>`

### Kata 2 — Manual

- Issue: `#30`
- Trial ID: `c1a52ff9328f47e280fbf65650ac5c82`
- Horário de início/fim: `2026-09-16T20:56:45Z` – `2026-09-16T21:02:51Z`
- Tempo e status: `365.99s`, `green`
- Resultado final dos testes: `9/9 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/c1a52ff9328f47e280fbf65650ac5c82/solucao.py`
- LOC / CC média / duplicação: `10 LOC / CC média 4,0 (máx. 4) / 0,0% duplicação`
- Observações: `<preencher>`

### Kata 3 — IA

- Issue: `#31`
- Trial ID: `445ecd175db145fa8e036a732e2bd08d`
- Horário de início/fim: `2026-09-16T20:47:29Z` – `2026-09-16T20:52:54Z`
- Tempo e status: `324.52s`, `green`
- Resultado final dos testes: `9/9 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/445ecd175db145fa8e036a732e2bd08d/solucao.py`
- LOC / CC média / duplicação: `16 LOC / CC média 3,0 (máx. 4) / 0,0% duplicação`
- Observações e número de interações com a IA (opcional): `<preencher>`

### Kata 4 — Manual

- Issue: `#32`
- Trial ID: `bee52a404549418498f55c6e0e2b2690`
- Horário de início/fim: `2026-09-16T21:10:37Z` – `2026-09-16T21:18:08Z`
- Tempo e status: `451.74s`, `green`
- Resultado final dos testes: `7/7 passando (100%)`
- Número de ciclos: `2`
- Caminho do código: `lab02/trials/results/solutions/bee52a404549418498f55c6e0e2b2690/solucao.py`
- LOC / CC média / duplicação: `11 LOC / CC média 3,0 (máx. 3) / 0,0% duplicação`
- Observações: `<preencher>`

## Incidentes e desvios do protocolo

- **Issue `#1` — Kata 1 IA — trial `c825af06fdf34b8383348801c0fc5782` — INVÁLIDO.** Interrompido manualmente com Ctrl+C após 331s e 13 ciclos, todos em 0/10 testes passando. Causa raiz identificada após inspeção do código: a função `normalizar_etiquetas` usava `yield` em vez de `return`, fazendo com que a função retornasse um objeto generator em vez de uma lista — `generator == lista` é sempre `False` em Python, então nenhum teste passava independentemente da lógica de normalização estar correta. Trial descartado; não usado na análise. Repetido sob a Issue `#22`.
- **Issue `#22` — Kata 1 IA — trial `8eee3cfc8eee49c98e5607ee320113bd` — INVÁLIDO.** Um processo `run_trial.py` anterior, iniciado às 20:02:55, não foi encerrado corretamente ao final de sua sessão (permaneceu em execução em segundo plano, fora da aba de terminal em uso). Esse processo completou seu próprio time-box de 35 minutos (2100s) às 20:37:55, sobrescrevendo o `trial.json` de um workspace recém-preparado sob o mesmo número de Issue, registrando `status: time-box` com 0/10 testes passando sem que o pesquisador estivesse ativamente trabalhando nele. Identificado via `ps aux` e conferência de horários no `trials.csv`. Trial descartado; não usado na análise. Repetido com sucesso na mesma Issue `#22` (workspace recriado após confirmação de que nenhum processo residual permanecia ativo), gerando o trial válido `3e505698c1834835b9610787e16f8e30` registrado na tabela acima.
- Nenhuma assistência de IA foi usada durante os trials Manual (Kata 2 e Kata 4).
- Nenhum arquivo de gabarito foi aberto ou copiado para qualquer workspace.

## Checklist antes do commit manual

- [ ] O piloto temporal foi feito com pessoas fora da amostra e não entrou nos CSVs oficiais.
- [ ] A matriz dos três integrantes contrabalança cada kata entre IA e Manual.
- [x] As quatro Issues existem no GitHub Projects e estão atribuídas a Vinicius.
- [x] Cada linha da tabela confere com `trials.csv`.
- [x] Cada `codigo_path` existe e corresponde ao snapshot final.
- [x] As quatro linhas de RQ3 foram coletadas a partir desses snapshots.
- [x] Nenhum arquivo de gabarito foi aberto ou copiado para um workspace.
- [x] O commit referencia a Issue correspondente.
