# Lab03 S02 — resultado final da validação

Execução em 20/10/2026, exclusivamente em `Laboratorio-3`, após pull por fast-forward.
HEAD inicial: `a8428d241b92743c30b25ff35d2ffaf2cb70358b`. Sem push, merge/rebase com main ou nova coleta.

## Avaliações, Kappa e consenso

Os três CSVs humanos passaram em **60/60 repositórios, 300/300 releases e zero erros**, com a mesma amostra/contexto. SHA-256 anteriores e posteriores coincidem; evidência em `data/validation/human_input_integrity.json`.

| Dimensão | Itens | Fleiss Kappa | Interpretação | Unanimidades | Maiorias 2×1 | Casos manuais |
|---|---:|---:|---|---:|---:|---:|
| project_type | 60 | 0,8628963153384747 | Quase perfeita | 52 | 8 | 0 |
| releases_represent_real_delivery | 60 | 0,15401301518438168 | Leve | 54 | 5 | 1 |
| corrective_release | 300 | 0,7352941176470585 | Substancial | 244 | 56 | 0 |

Kappa usa votos originais, antes do consenso. Há **70 divergências**, 350 unanimidades, 69 maiorias e um caso manual. A interpretação segue a escala implementada no projeto. Concordância bruta e Kappa não são intercambiáveis.

**Resolução humana aplicada:** `armbian/build`, dimensão `releases_represent_real_delivery`; Islayder=`no`, Fernanda=`uncertain`, Vinicius=`yes`; consenso final **`no`**, reviewer **Islayder**. O humano justificou que “Armbian Weekly digest” resume o desenvolvimento do framework de build, enquanto imagens para usuários são distribuídas por outros canais oficiais. A justificativa integral está em `data/gold_sample/manual_resolutions.csv`. Nenhum voto original foi alterado.

`gold_sample_consensus.csv` valida 60×5 sem erros; **zero pendências manuais**. A primeira execução e seu template vazio estão preservados nos diretórios `pre_manual/` e em `lab03_s02_validation_pre_manual.md`. Kappa é byte a byte idêntico antes/depois da resolução. Divergências preservam os votos originais; `consensus_votes.csv` incorpora a resolução autorizada.

## Validação da heurística (#58)

| Versão | TP | FP | FN | TN | Precision | Recall | F1 |
|---|---:|---:|---:|---:|---:|---:|---:|
| v1 | 96 | 156 | 14 | 34 | 0.380952 | 0.872727 | 0.530387 |
| v2 | 106 | 115 | 4 | 75 | 0.479638 | 0.963636 | 0.640483 |
| v3 | 48 | 5 | 62 | 185 | 0.905660 | 0.436364 | 0.588957 |
| v4 | 57 | 9 | 53 | 181 | 0.863636 | 0.518182 | 0.647727 |
| v5 | 83 | 36 | 27 | 154 | 0.697479 | 0.754545 | 0.724891 |

**v5 aceita**, primeira com F1≥0,70; classe positiva `yes`. Nenhum ajuste após aceitação. Cada execução preserva código, política, fontes, hashes e previsões. Mudanças generalizáveis e justificativas em `docs/s02_corrective_validation.md`. Não há regras por identidade/rótulo no classificador. Cinco avaliações na mesma amostra geram otimismo de seleção: validação interna, sem teste externo.

## CFR(b) e completude das métricas

O grupo confirmou a definição antes do cálculo: qualquer corretiva posterior em até sete dias, não apenas a imediatamente seguinte. Censura final incondicional a partir de `2026-09-24T00:00:00Z`; originais censurados ainda podem ser evidência para anteriores. Ausência de predecessora não exclui o original. Sem positiva conhecida, classificação posterior indisponível gera caso não calculável. Política `any_corrective_7d_v1`, heurística v5.

**CFR(b): 311 válidos, zero ausentes.** Partição das 27.152 releases: 20.038 falhas, 6.406 não falhas, 677 censuradas e 31 não calculáveis. Denominador global 26.444; razões calculadas individualmente por repo. As 180 classificações com contexto insuficiente estão marcadas na população; não se confundem com os 31 originais afetados no denominador.

| Métrica nos 311 repos | Válidos | Ausentes | Motivo |
|---|---:|---:|---|
| Deployment frequency (semana/mês) | 311 | 0 | — |
| Lead time por release | 261 | 50 | 29 comparison_error, 21 metric_error |
| Lead time por commit | 261 | 50 | Mesmos erros de enriquecimento |
| CFR(a) | 311 | 0 | — |
| CFR(b) | 311 | 0 | — |
| Recovery time (mediana) | 286 | 25 | 23 sem episódios, 2 somente censurados |
| Proporção de censura de recovery | 288 | 23 | Nenhum episódio; denominador nulo |

Auditoria de 311 linhas/48 colunas: zero duplicatas e zero erros nos tipos/domínios, fontes, fórmulas, quartis/IQR e partição de CFR(b) verificados. Não calculáveis/censuras não foram imputados como zero. As outras 46 colunas do HEAD inicial foram preservadas, assim como fontes coletadas e arquivos humanos. Variantes e entradas para as combinações de RQ07 estão persistidas; as análises da S03 não foram antecipadas.

## Reprodução, testes e metodologia

```powershell
python -m src.corrective_population
python -m src.cfr_delivery
python -m src.s02_dataset
python -m src.s02_quality
python -m pytest --cov=src --cov-report=term-missing --cov-fail-under=96
```

**523 testes aprovados**, cobertura **97.97%**, piso 96% inalterado. Resumo em `data/validation/test_summary_s02.json`. Execução local Windows/Python 3.13.15; nenhum workflow remoto foi acionado. A dependência já fixada scikit-learn foi instalada na .venv. Classificação/CFR recusam sobrescrever resultados; para reprodução, usar destinos novos conforme a documentação.

Metodologia consolidada: `article/metodologia_s02.md`; o fragmento de Fernanda foi preservado e identificado como histórico. Dicionário, documentação de coleta/consolidação/validação e relatórios refletem os resultados reais. Estados iniciais de espera e de consenso pendente foram preservados como históricos.

## Gates finais

- [x] 311 repositórios, dataset e dicionário presentes.
- [x] Três arquivos humanos completos, mesma amostra 60×5 e SHA-256 preservados.
- [x] Kappa nas três dimensões, 70 divergências e consenso completo.
- [x] Uma resolução humana registrada, zero casos pendentes.
- [x] Heurística avaliada, matriz/precision/recall/F1 persistidos; v5≥0,70.
- [x] CFR(a/b), variantes e censuras persistidos, fontes rastreáveis.
- [x] Metodologia atualizada e estado histórico separado do atual.
- [x] Todos os testes passam e cobertura≥96%.

**S02 tecnicamente concluída**, com as indisponibilidades de enriquecimento e limitações metodológicas descritas. Commits e limpeza do working tree são conferidos ao encerrar a execução; nenhum push faz parte desta entrega.
