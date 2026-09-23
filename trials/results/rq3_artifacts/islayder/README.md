# Artefatos finais de Islayder para RQ3

Esta pasta reúne os quatro códigos analisados estruturalmente para Islayder.

- #21 e #25: soluções criadas a partir dos enunciados e testes de aceitação versionados, sem consulta a gabaritos.
- #24 e #26: cópias rastreáveis dos snapshots Manual já registrados no commit `b92755d`.
- `manifest.csv`: vínculo entre participante, Issue, kata, tratamento, código e testes.

Os IDs `RQ3-ISLAYDER-*` identificam artefatos estruturais e não substituem os IDs do runner. As métricas são coletadas por `lab02/metrics/run_metrics.py` e gravadas em `lab02/metrics/results/metrics.csv`.

## Verificação dos artefatos IA

Execute cada módulo de testes separadamente para evitar colisão entre os dois
arquivos chamados `test_solucao.py`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q lab02\trials\results\rq3_artifacts\islayder\issue-21-kata1-ia\test_solucao.py
.\.venv\Scripts\python.exe -m pytest -q lab02\trials\results\rq3_artifacts\islayder\issue-25-kata3-ia\test_solucao.py
```

Os resultados esperados e confirmados são, respectivamente, `10 passed` e
`9 passed`. As cópias de `test_solucao.py` preservam o conteúdo dos testes
originais; nenhuma alteração foi feita em `src/katas/`.

Os comandos de reprodução das métricas estão documentados em
`lab02/metrics/README.md`. O script `lab02.analysis.analyze_rq3` valida a
existência dos arquivos deste manifesto, a correspondência com `metrics.csv`,
a completude das métricas e a exclusão de IDs `SIM-*` da seleção final.
