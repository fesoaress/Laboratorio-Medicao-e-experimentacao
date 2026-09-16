# Lab02 S02 — cenário sintético de Islayder

**SIMULAÇÃO. Estes dados não foram produzidos por Islayder e não são resultados experimentais oficiais.** Eles servem apenas para exercitar tabelas, junções e análises antes das execuções reais.

`generate.py` define quatro cenários hipotéticos para as Issues #21, #24, #25 e #26. Os tempos, a evolução dos testes por ciclo, LOC, complexidade e duplicação foram escolhidos como fixtures. A quantidade total de testes é lida dos arquivos de aceitação de cada kata. O script calcula `failed` e a taxa de sucesso a partir desses valores e verifica a coerência dos ciclos. **Ele não executa `run_trial`, não roda os testes de aceitação e não usa Radon nem jscpd para produzir essas métricas.** Não há código final nem snapshots associados.

Os CSVs têm nomes e colunas `simulated_*`, `simulation_id` iniciado por `SIM-`, `source_kind=synthetic_fixture` e `participant_label=SIMULACAO_ISLAYDER`. `planned_treatment` indica a alocação pretendida; nenhum tratamento Manual ou IA foi aplicado nesta simulação. O status `green` ou `time-box` é apenas o desfecho hipotético do cenário.

Arquivos gerados:

- `simulated_trials.csv`: uma linha por cenário;
- `simulated_trial_cycles.csv`: progressão hipotética dos ciclos;
- `simulated_metrics.csv`: métricas estruturais hipotéticas.

Para regenerar a fixture, a partir da raiz do repositório no Windows:

```powershell
.\.venv\Scripts\python.exe -m lab02.simulations.islayder_s02.generate
```

Nenhum desses CSVs deve ser copiado para `lab02/trials/results/` ou `lab02/metrics/results/`, usado para inferir o efeito de IA ou Manual, ou considerado para fechar a Sprint 02. Os trials oficiais continuam dependendo de execuções reais do participante e da coleta de métricas sobre seus snapshots.
