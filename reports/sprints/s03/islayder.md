# Lab02 S03 — contribuição individual de Islayder

**Issue:** #33 — RQ1, RQ2 e inovação.  
**Responsabilidade:** auditar os dados da S02, analisar tempo, testes e evolução por ciclo e documentar os resultados.

## Dados finais de Islayder

Os resultados de #21 e #25 foram informados pelo participante após execuções com o Gemini no celular. Os totais de testes foram conferidos diretamente nos arquivos de aceitação: 10 testes no Kata 1 e 9 testes no Kata 3. Os resultados de #24 e #26 permanecem os registrados pelo runner.

| Issue | Kata | Tratamento | Tempo (s) | Testes | Falhando | Ciclos | Status |
|---|---|---|---:|---:|---:|---:|---|
| #21 | `kata1_normalizador_etiquetas` | IA | 75,00 | **10/10** | 0 | 1 | `green` |
| #24 | `kata2_balanceamento_turnos` | Manual | 127,17 | **9/9** | 0 | 1 | `green` |
| #25 | `kata3_compactador_sensor` | IA | 150,00 | **9/9** | 0 | 1 | `green` |
| #26 | `kata4_manutencao_preditiva` | Manual | 208,02 | **7/7** | 0 | 2 | `green` |

## RQ1 — Tempo

| Tratamento | n | Média (s) | Mediana (s) | Q1 (s) | Q3 (s) | IQR (s) |
|---|---:|---:|---:|---:|---:|---:|
| IA | 2 | 112,500 | 112,500 | 93,750 | 131,250 | 37,500 |
| Manual | 2 | 167,595 | 167,595 | 147,383 | 187,808 | 40,425 |

A média e a mediana de IA ficaram **55,095 s abaixo** de Manual, diferença descritiva de **32,87%**. Com somente um par de medianas por participante no recorte individual, não há base para interpretação inferencial do Wilcoxon.

## RQ2 — Testes

| Tratamento | Trials green | Passando | Falhando | Taxa final |
|---|---:|---:|---:|---:|
| IA | 2/2 | **19/19** | 0 | 100% |
| Manual | 2/2 | **16/16** | 0 | 100% |

Os totais absolutos, e não apenas o percentual, mostram que os dois tratamentos terminaram sem falhas de aceitação.

## Inovação — Ciclos até green

Os quatro trials somaram **5 ciclos**. IA chegou a `green` em um ciclo nos dois katas, com mediana de **1,0 ciclo**. Manual usou um e dois ciclos, com mediana de **1,5 ciclo**. O último ciclo de todos os trials terminou com 100% dos testes passando.

## RQ3 — Qualidade estrutural

Foram criados artefatos finais rastreáveis em `lab02/trials/results/rq3_artifacts/islayder/` e o coletor estrutural foi executado sobre os quatro códigos reais. Os registros finais usam IDs `RQ3-ISLAYDER-*`, `source_kind=observed` e caminhos de código verificáveis; nenhum ID `SIM-*` entra na análise.

| Issue | Tratamento | LOC | CC média | CC máxima | Duplicação | Linhas duplicadas | Blocos duplicados | Funções |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| #21 | IA | 15 | 4,0 | 4 | 0% | 0 | 0 | 1 |
| #24 | Manual | 6 | 4,0 | 4 | 0% | 0 | 0 | 1 |
| #25 | IA | 27 | 2,6667 | 4 | 0% | 0 | 0 | 3 |
| #26 | Manual | 11 | 3,0 | 3 | 0% | 0 | 0 | 1 |

Para Islayder, a mediana de LOC foi 21,0 em IA e 8,5 em Manual; a mediana de CC média foi 3,3334 em IA e 3,5 em Manual. A duplicação foi zero nos quatro códigos.

## Fontes e limites

- Totais de aceitação: [`src/katas/kata1_normalizador_etiquetas/test_solucao.py`](../../../src/katas/kata1_normalizador_etiquetas/test_solucao.py) e [`src/katas/kata3_compactador_sensor/test_solucao.py`](../../../src/katas/kata3_compactador_sensor/test_solucao.py).
- Relatório individual completo: [`reports/sprints/lab02_s02/islayder.md`](../lab02_s02/islayder.md).
- #21 e #25: tempo, ciclo, status e aprovação integral informados pelo participante.
- #24 e #26: dados preservados dos registros do runner.
- RQ3: métricas reproduzíveis em [`metrics.csv`](../../../lab02/metrics/results/metrics.csv) e vínculo dos artefatos em [`manifest.csv`](../../../lab02/trials/results/rq3_artifacts/islayder/manifest.csv).
- Os katas diferem entre tratamentos; os resultados sustentam comparação descritiva, não causal.
