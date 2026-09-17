# Lab02 S02 — cenário sintético de Islayder

**SIMULAÇÃO. Estes dados não foram produzidos por Islayder e não são resultados experimentais oficiais.** Eles servem apenas para exercitar tabelas, junções e análises antes das execuções reais.

`generate.py` define quatro cenários hipotéticos para as Issues #21, #24, #25 e #26. Os tempos, a evolução dos testes por ciclo, LOC, complexidade e duplicação foram escolhidos como fixtures. A quantidade total de testes é lida dos arquivos de aceitação de cada kata. O script calcula `failed` e a taxa de sucesso a partir desses valores e verifica a coerência dos ciclos. **Ele não executa `run_trial`, não roda os testes de aceitação e não usa Radon nem jscpd para produzir essas métricas.** Não há código final nem snapshots associados.

Os CSVs têm nomes e colunas `simulated_*`, `simulation_id` iniciado por `SIM-`, `source_kind=observed_simulated` e `participant_label=SIMULACAO_ISLAYDER`. `planned_treatment` indica a alocação pretendida; nenhum tratamento Manual ou IA foi aplicado nesta simulação. O status `green` ou `time-box` é apenas o desfecho hipotético do cenário.

Arquivos gerados:

- `simulated_trials.csv`: uma linha por cenário;
- `simulated_trial_cycles.csv`: progressão hipotética dos ciclos;
- `simulated_metrics.csv`: métricas estruturais hipotéticas.

Para regenerar a fixture, a partir da raiz do repositório no Windows:

```powershell
.\.venv\Scripts\python.exe -m lab02.simulations.islayder_s02.generate
```

Para ensaiar um pipeline que lê os CSVs consolidados, cada cenário pode ser exportado com `python -m lab02.simulations.islayder_s02.export_to_results --issue 21` (troque o número por 24, 25 ou 26). A exportação preserva as linhas existentes e identifica as novas com `trial_id=SIM-*`, `source_kind=observed_simulated` e `status=simulated-*`. Não há horário de execução, snapshot nem JSON de métricas: tempo, ciclos, testes e métricas continuam **hipotéticos**. A coluna `analysis_error` das métricas e `erro_execucao` dos trials registram essa origem.

Qualquer análise empírica da Sprint 02 deve filtrar `source_kind=observed` e validar separadamente os cenários `source_kind=observed_simulated`. A presença desses cenários no CSV consolidado não equivale à execução humana dos quatro trials por Islayder nem fecha a Sprint 02 como coleta observada.
