# Execução e contratos — Sprint 03

## Reexecutar análises offline

Python 3.12+ e as versões de `requirements-dev.txt`:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
$env:MPLCONFIGDIR = Join-Path $env:TEMP 'lab03-mpl'
.\.venv\Scripts\python.exe -m src.s03
.\.venv\Scripts\python.exe -m pytest --cov=src --cov-report=term-missing --cov-fail-under=96
```

O comando não lê `.env`, não faz consultas ao GitHub e não reescreve S02,
rótulos ou consenso. Somente saídas derivadas S03 são regeneradas. O plano
e os shards de comparações complementares versionados tornam a RQ07
reexecutável sem baixar novamente os 311 repositórios. Os manifests
registram versões, seeds, fontes, SHA-256 e o estado das análises; o estado
`core_complete_rq07_pending`, reservado a `--core-only`, não significa S03 completa.

Para comparar duas execuções, use pastas de saídas/relatórios/figuras
diferentes (`--output`, `--reports`, `--figures`), copie o plano comprimido e
`variant_context/` para a nova pasta e compare as tabelas CSV byte a byte.
Datas de criação e IDs SVG foram estabilizados: as 18 tabelas e 27 arquivos
de imagem foram reproduzidos byte a byte no mesmo ambiente. Versões de
bibliotecas/fontes e sistema operacional podem afetar novas renderizações.
Fixtures sintéticas dos testes não são os dados empíricos.

## Coleta complementar autorizada

A execução real utilizou os componentes próprios S01/S02, `urllib`, cache
REST/GraphQL e o Git completo do WPT, sem PyGithub. Cache e checkpoints
ficam em `data/raw/s03/`, ignorados. O `.env` também é ignorado; somente
o processo autenticado recebe `GITHUB_TOKEN`, sem registrá-lo.

O plano inicial possui 9.980 pares únicos não disponíveis no export estável,
incluindo pares resolvíveis pelo Git local e a sobreposição C2/C3. Esse número
não é o de chamadas novas à API. As lacunas diagnosticadas originalmente
eram 1.682 intervalos C2/83 repositórios e 4.456 C3/150, descontados cache e
Git. O refinamento de fronteira verifica predecessoras anteriores à janela:
não adiciona entregas fora da janela às métricas. Esses patches ficam
separados do plano inicial, preservando as evidências anteriores.

```powershell
# Apenas para retomar a coleta autorizada, com GITHUB_TOKEN já no processo:
.\.venv\Scripts\python.exe -m src.s03_collect
.\.venv\Scripts\python.exe -m src.s03_predecessors
.\.venv\Scripts\python.exe -m src.s03_collect --export-only
```

Não é necessário executar essa sequência para repetir a análise offline.
Falhas de comparação não são automaticamente reconsultadas na retomada;
os checkpoints preservam o diagnóstico. Eventual nova tentativa deve
preservar o registro anterior em outro diretório e documentar seu motivo.

## Dicionário das saídas

Todos os CSVs ficam em `data/processed/s03/`. Vazio significa não calculável.
Datas são UTC. Frações pertencem a [0,1], horas são decimais.

| Artefato | Grão e campos principais |
|---|---|
| `descriptive.csv` | Métrica; `n,missing,median,q1,q3,iqr,minimum,maximum,unit,rq` |
| `classifications.csv` | Repositório; categorias individuais e `general` C1 |
| `dora_distribution.csv` | Métrica×categoria; contagens válidas e ausentes |
| `spearman.csv` | Desfecho CFR; `rho,p,n,p_permutation,p_permutation_holm,status` |
| `factor_tests.csv` | Fator×métrica; família, teste, estatística, p, p_Holm, efeito, n |
| `factor_groups.csv` | Fator×métrica×grupo; n, ausentes, mediana e IQR |
| `factor_cutpoints.csv` | Cortes globais e política de empates |
| `bootstrap.csv` | Estimativa; IC95%, réplicas válidas, seed e método |
| `variant_plan.json.gz` | Janela, repositórios, eventos factuais, pares por SHA e auditoria de fronteira |
| `variant_context/part-*.jsonl.gz` | Comparação por linha; SHAs, fonte, status, commits e eventual erro; lotes de até 1.000 pares |
| `variant_metrics.csv` | Repositório×C2/C3; frequência, CFR, LT próprio, observações, status e erros |
| `variant_classifications.csv` | Repositório; DF/LT/CFR/recuperação/geral de C1/C2/C3 |
| `sensitivity.csv` | Par de combinações×métrica; n pareado, mudanças, %, Kappa linear e status |
| `sensitivity_common.csv` | Mesmas comparações na interseção das três categorias gerais válidas |
| `sensitivity_exclusions.csv` | Repositórios excluídos de cada par geral e qual lado ficou ausente |
| `rework_summary.csv` | Mediana, quartis, IQR e completude da taxa de retrabalho |
| `c2_predictions.csv` | Evento release/pré-release; previsão v5, usabilidade e chave de comparação |
| `c2_cfr_events.csv` | Evento original C2; falha, censura, evidência corretiva e contexto insuficiente |
| `comparisons_provenance.csv` | Par único; fonte, SHAs, URL, transporte, status, erro e número de commits |
| `rework.csv` | Repositório; corretivas conhecidas, desconhecidas, taxa quando completa e limites |

`reports/s03/audit.json` persiste a conferência independente S02.
`reports/s03/manifest.json` registra a execução estatística. As figuras
em `figures/s03/` têm versões PNG, SVG e PDF. A metodologia completa,
incluindo limites DORA, fórmulas e famílias de Holm, está em
`article/metodologia_s03.md`. Não interpretar `observations` de um LT
invalidado como denominador de uma mediana válida.

Limitações de processo e ações manuais do Projects estão em
`reports/s03/process.md` e na Issue #73. Resultados técnicos não suprem
a comprovação das contribuições individuais.
