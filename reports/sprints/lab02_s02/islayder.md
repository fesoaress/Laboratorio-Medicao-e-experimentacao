# Lab02 S02 — Islayder

**SPRINT 02 AINDA PENDENTE.** Na auditoria de 16/09/2026, não havia trial oficial de Islayder para nenhuma das quatro Issues. A preparação abaixo não representa execução experimental.

## Ambiente e protocolo

- Participante e alocação: Islayder; Katas 1 e 3 com IA, Katas 2 e 4 com tratamento Manual.
- Time-box: 35 minutos por trial.
- Ambiente usado apenas na preparação: Windows, Python 3.13.15 em `.venv`, pytest 9.1.1 e Radon 6.0.1. Node.js e npm não estavam disponíveis neste ambiente; serão necessários para coletar a duplicação com jscpd.
- IDE/editor, assistente de IA e versão/plano, data e ambiente das execuções oficiais: **pendentes de registro por Islayder**.
- Piloto temporal com pessoas fora da amostra e matriz contrabalanceada do grupo: **não comprovados nesta auditoria**; confirmar antes de iniciar os trials.

## Rastreabilidade dos trials

`—` significa que ainda não existe valor experimental. Os CSVs oficiais contêm zero linhas para as Issues #21, #24, #25 e #26; por isso não há `trial_id`, tempo, testes, taxa, ciclos nem métricas a relatar.

| Issue | Kata | Tratamento | Trial ID | Resultado | Tempo (s) | Testes (passando/falhando) | Taxa | Ciclos | LOC | CC média | Duplicação | Arquivos oficiais gerados |
|---|---|---|---|---|---:|---|---:|---:|---:|---:|---:|---|
| #21 | `kata1_normalizador_etiquetas` | IA | — | **PENDENTE — execução oficial pelo participante** | — | — | — | — | — | — | — | Nenhum |
| #24 | `kata2_balanceamento_turnos` | Manual | — | **PENDENTE — execução oficial pelo participante** | — | — | — | — | — | — | — | Nenhum |
| #25 | `kata3_compactador_sensor` | IA | — | **PENDENTE — execução oficial pelo participante** | — | — | — | — | — | — | — | Nenhum |
| #26 | `kata4_manutencao_preditiva` | Manual | — | **PENDENTE — execução oficial pelo participante** | — | — | — | — | — | — | — | Nenhum |

## Preparação local concluída

Os quatro comandos `prepare_trial` foram executados no Windows com `.\.venv\Scripts\python.exe`. Cada workspace contém somente `solucao.py`, `test_solucao.py` e `trial.json` com status `prepared`. São pastas transitórias ignoradas pelo Git. **Nenhum `run_trial` foi executado, nenhum cronômetro foi iniciado e nenhum CSV oficial foi alterado.**

| Issue | Workspace preparado |
|---|---|
| #21 | `lab02/trials/workspaces/islayder/kata1_normalizador_etiquetas_ia_issue-21` |
| #24 | `lab02/trials/workspaces/islayder/kata2_balanceamento_turnos_manual_issue-24` |
| #25 | `lab02/trials/workspaces/islayder/kata3_compactador_sensor_ia_issue-25` |
| #26 | `lab02/trials/workspaces/islayder/kata4_manutencao_preditiva_manual_issue-26` |

## Como Islayder fecha as pendências

1. Confirmar o piloto temporal, a matriz do grupo, as quatro Issues e a configuração dos tratamentos. Instalar Node.js/npm e executar `npm ci` em `lab02\metrics` antes da coleta estrutural. Nos trials Manual, trabalhar sem assistente; nos trials IA, registrar o assistente e a versão utilizados.
2. Executar pessoalmente cada trial, **um por vez**, a partir da raiz do repositório. Abrir no editor somente o workspace correspondente e editar somente `solucao.py`. Usar os comandos abaixo na ordem prevista; pressionar ENTER no runner para registrar cada ciclo. Se o workspace local não existir em outro checkout, recriá-lo antes com `python -m lab02.trials.prepare_trial` e os mesmos parâmetros da tabela.

   ```powershell
   .\.venv\Scripts\python.exe -m lab02.trials.run_trial --workspace lab02\trials\workspaces\islayder\kata1_normalizador_etiquetas_ia_issue-21
   .\.venv\Scripts\python.exe -m lab02.trials.run_trial --workspace lab02\trials\workspaces\islayder\kata2_balanceamento_turnos_manual_issue-24
   .\.venv\Scripts\python.exe -m lab02.trials.run_trial --workspace lab02\trials\workspaces\islayder\kata3_compactador_sensor_ia_issue-25
   .\.venv\Scripts\python.exe -m lab02.trials.run_trial --workspace lab02\trials\workspaces\islayder\kata4_manutencao_preditiva_manual_issue-26
   ```

3. Após **cada** execução real, conferir `trial_id`, Issue, participante, kata, tratamento, status, tempo, testes, taxa e ciclos em `lab02/trials/results/trials.csv` e `trial_cycles.csv`. Confirmar que `codigo_path` aponta para `solucao.py` e `test_solucao.py` do snapshot final. Um trial interrompido ou com erro precisa ser identificado como tal; a repetição exige nova Issue, conforme o protocolo.
4. Para cada trial oficial concluído, calcular LOC, CC média e duplicação **somente do `codigo_path` real**, com o `trial_id` e a Issue correspondentes. Exemplo de comando para #21; trocar kata, tratamento, `trial_id`, `codigo_path` e Issue para os demais:

   ```powershell
   .\.venv\Scripts\python.exe lab02\metrics\run_metrics.py <codigo_path_de_trials.csv> --participant Islayder --kata kata1_normalizador_etiquetas --treatment IA --trial-id <trial_id_de_trials.csv> --issue 21
   ```

5. Atualizar esta tabela e registrar os arquivos gerados para cada Issue: `trials.csv`, `trial_cycles.csv`, `results/solutions/<trial_id>/solucao.py`, `results/solutions/<trial_id>/test_solucao.py`, `metrics/results/metrics.csv` e o JSON detalhado de métricas local. Validar os dados e fazer commits rastreáveis por Issue antes de declarar a sprint fechada.

## Validação desta preparação

- `pytest -q lab02\trials\tests lab02\metrics\tests`: **20 passaram**.
- `python -m compileall lab02`: **passou**.
- Auditoria de schema e junção dos CSVs: 6 trials, 19 ciclos e 4 linhas de métricas existentes, todos de Vinicius; nenhum de Islayder. Os `trial_id` e pares `(trial_id, ciclo)` são únicos, os snapshots apontados existem e seus testes conferem com os arquivos de aceitação dos respectivos katas.
- Achados fora do escopo de Islayder, preservados: a Issue #22 de Vinicius aparece em dois trials distintos; os quatro `json_path` de métricas dele apontam para JSONs locais ausentes neste checkout (esses JSONs são ignorados pelo Git). Não há base para classificar ou remover qualquer registro dele como piloto.
- Nenhum resultado experimental de Islayder foi criado ou fabricado. Nenhum arquivo de `src/katas/gabarito/` foi aberto, copiado ou utilizado nesta preparação.
