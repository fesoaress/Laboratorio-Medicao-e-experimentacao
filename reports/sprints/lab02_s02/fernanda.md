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
| 1 | `#19` | `kata2_balanceamento_turnos` | IA | `0.88` | `green` | `9` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/5e85c97fc84f4819a10aa87970316abf/solucao.py` | Green no 1º ciclo |
| 2 | `#27` | `kata1_normalizador_etiquetas` | Manual | `1.77` | `green` | `10` | `0` | `100.0%` | `2` | `lab02/trials/results/solutions/31c7f16ce79c478ab8f81cd8628e6e3c/solucao.py` | 30% no ciclo 1, green no ciclo 2 |
| 3 | `#29` | `kata4_manutencao_preditiva` | IA | `0.94` | `green` | `7` | `0` | `100.0%` | `1` | `lab02/trials/results/solutions/bd057b8dcaef41a6a9503c053b9d57f3/solucao.py` | Green no 1º ciclo |
| 4 | `#28` | `kata3_compactador_sensor` | Manual | `1.84` | `green` | `9` | `0` | `100.0%` | `2` | `lab02/trials/results/solutions/4dfbe8c44c964a65ae003d35d6a60754/solucao.py` | 44,44% no ciclo 1, green no ciclo 2 |

Fonte dos valores: `lab02/trials/results/trials.csv`. Evolução por ciclo em `lab02/trials/results/trial_cycles.csv`. Métricas RQ3 em `lab02/metrics/results/metrics.csv`.

### Vínculo com as Issues do GitHub

Cada trial é vinculado à Issue da S02 que endereça o seu kata: Kata 1 → `#27`, Kata 2 → `#19`, Kata 3 → `#28`, Kata 4 → `#29`. As quatro estão criadas no repositório e atribuídas a `fesoaress`, e são as mesmas referenciadas na mensagem do commit de entrega.

Duas correções de rastreabilidade em relação à versão anterior deste relatório:

- Os CSVs e as tabelas citavam as Issues `#33`–`#36`, que nunca existiram: a numeração do repositório vai até `#32`. `trials.csv`, `trial_cycles.csv`, `metrics.csv` e este relatório passaram a usar `#19`, `#27`, `#28` e `#29`.
- Os títulos das quatro Issues no GitHub descrevem o tratamento oposto ao que foi executado — `#27` está intitulada "Kata 1 - IA", mas o kata 1 foi feito Manual, e assim por diante. Os CSVs e este relatório registram o tratamento efetivamente aplicado, que é o que produz o contrabalanceamento frente a Islayder e Vinicius (ambos executaram Kata 1 e 3 com IA, Kata 2 e 4 Manual). Renomear os títulos das Issues no GitHub para o tratamento executado continua pendente.

## Registro detalhado por trial

### Trial 1 — Kata 2 — IA

- Issue: `#19`
- Trial ID: `5e85c97fc84f4819a10aa87970316abf`
- Horário de início/fim: `2026-09-17T00:01:24Z` – `2026-09-17T00:01:25Z`
- Tempo e status: `0.88s`, `green`
- Resultado final dos testes: `9/9 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/5e85c97fc84f4819a10aa87970316abf/solucao.py`
- LOC / CC média / duplicação: `4 LOC / CC média 4,0 (máx. 4) / 0,0% duplicação`
- Observações: assistência de IA utilizada.

### Trial 2 — Kata 1 — Manual

- Issue: `#27`
- Trial ID: `31c7f16ce79c478ab8f81cd8628e6e3c`
- Horário de início/fim: `2026-09-17T00:01:25Z` – `2026-09-17T00:01:27Z`
- Tempo e status: `1.77s`, `green`
- Resultado final dos testes: `10/10 passando (100%)`
- Número de ciclos: `2` (ciclo 1: 3/10 = 30%; ciclo 2: 10/10 = 100%)
- Caminho do código: `lab02/trials/results/solutions/31c7f16ce79c478ab8f81cd8628e6e3c/solucao.py`
- LOC / CC média / duplicação: `14 LOC / CC média 6,0 (máx. 6) / 0,0% duplicação`
- Observações: sem assistência de IA.

### Trial 3 — Kata 4 — IA

- Issue: `#29`
- Trial ID: `bd057b8dcaef41a6a9503c053b9d57f3`
- Horário de início/fim: `2026-09-17T00:01:27Z` – `2026-09-17T00:01:28Z`
- Tempo e status: `0.94s`, `green`
- Resultado final dos testes: `7/7 passando (100%)`
- Número de ciclos: `1`
- Caminho do código: `lab02/trials/results/solutions/bd057b8dcaef41a6a9503c053b9d57f3/solucao.py`
- LOC / CC média / duplicação: `10 LOC / CC média 3,0 (máx. 3) / 0,0% duplicação`
- Observações: assistência de IA utilizada.

### Trial 4 — Kata 3 — Manual

- Issue: `#28`
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
| Kata 2 IA | #19 | 1 | 100% |
| Kata 1 Manual | #27 | 2 | 30% → 100% |
| Kata 4 IA | #29 | 1 | 100% |
| Kata 3 Manual | #28 | 2 | 44,44% → 100% |

## Incidentes e desvios do protocolo

- Nenhum trial interrompido ou time-box.
- Issues `#19`, `#27`, `#28` e `#29` vinculadas aos trials conforme a alocação contrabalanceada.

### Ressalva de validade dos quatro trials

Os dados desta rodada estão registrados como `observed` nos CSVs, mas duas características os tornam inadequados para sustentar conclusões sobre tempo de execução, e isso precisa ser lido junto com qualquer análise que os utilize:

- Os tempos registrados vão de `0.88s` a `1.84s` por trial, com os quatro trials concluídos dentro de um intervalo de seis segundos (`00:01:24Z` a `00:01:30Z`). Não são tempos compatíveis com resolução humana de um kata sob time-box de 35 minutos; para comparação, os trials de Vinicius levaram de 50 s a 452 s.
- Os snapshots finais de Kata 2 (IA) e Kata 1 (Manual) são byte-a-byte idênticos aos gabaritos `src/katas/gabarito/kata2_solucao_referencia.py` e `src/katas/gabarito/kata1_solucao_referencia.py`, verificado por SHA-256. Os snapshots de Kata 3 e Kata 4 diferem do gabarito apenas em nomes de variáveis e estrutura de laço, permanecendo semanticamente equivalentes. A afirmação anterior de que nenhum gabarito foi aberto ou copiado para o workspace não se sustenta e foi removida.

O conjunto indica que a rodada funcionou como ensaio de validação do instrumento de coleta, e não como execução experimental cronometrada. As métricas estruturais da RQ3 sobre esses snapshots são reprodutíveis e foram reconferidas com `run_metrics.py` (valores idênticos aos já registrados), mas medem código de referência, não código produzido por um participante sob tratamento. Para que a comparação IA vs. Manual da Fernanda tenha validade, os quatro trials precisam ser reexecutados sob o protocolo cronometrado.

## Checklist antes do commit manual

- [x] A matriz dos três integrantes contrabalança cada kata entre IA e Manual.
- [x] Quatro trials executados por Fernanda (2 IA + 2 Manual).
- [x] Cada linha da tabela confere com `trials.csv`.
- [x] Cada `codigo_path` existe e corresponde ao snapshot final.
- [x] Quatro linhas de RQ3 coletadas em `metrics.csv`.
- [x] Evolução por ciclo registrada em `trial_cycles.csv`.
- [x] Issues `#19`, `#27`, `#28` e `#29` criadas no GitHub e atribuídas a `fesoaress` (confirmado na API de Issues do repositório; as quatro seguem com status `open`).
- [x] Commit referenciando as Issues publicado: `30931dc`, presente em `origin/Laboratorio-2`.
- [ ] Renomear os títulos das quatro Issues no GitHub para o tratamento executado (hoje descrevem o oposto).
- [ ] Reexecutar os quatro trials sob o protocolo cronometrado, conforme a ressalva de validade acima.

A mensagem do commit `30931dc` descreve os pares kata/tratamento pelos títulos das Issues, e não pelo que foi executado, e repete "Kata3" no lugar de "Kata4". A alocação correta é a das tabelas deste relatório.

Sobre os JSONs por trial da RQ3: `run_metrics.py` gera um JSON detalhado por execução em `lab02/metrics/results/`, referenciado pela coluna `json_path` do `metrics.csv`. Esses arquivos são ignorados pelo `.gitignore` (linha `lab02/metrics/results/*_*.json`) por serem auditoria local, então não aparecem em um clone novo — o CSV consolidado é o artefato versionado. Instruções de regeração em `lab02/trials/FERNANDA_S02.md`.

Procedimento operacional: `lab02/trials/FERNANDA_S02.md`.
