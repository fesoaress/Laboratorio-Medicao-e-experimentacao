# Auditoria técnica final — Lab03S03

## 1. Branch e histórico

Branch `Laboratorio-3`; HEAD inicial `0fb56f6133ddfa0b47bbe93415c90ac767ead396`; HEAD imutável do código/artefatos de cálculo `da3b4175b06ea45162c9386c23ed42f2e1d4ebd6`. Commits documentais posteriores registram artigo e evidências. O SHA publicado e o CI remoto estão em `ci_s03.json`, e o HEAD documental mais recente no histórico Git.

`main` permanece `07df90fc3a418c4a149b30ba6dd1a151bf396b8b`. Não houve merge/rebase com main, force push, alteração da seleção ou sobrescrita S01/S02. Os cinco commits S02 foram publicados com push normal após auditoria; seu CI passou (523 testes; 97,97%).

## 2. Integridade S02, rótulos e consenso

Auditoria `valid`: 311 identidades únicas, zero erros de consolidação; fórmulas e faltantes reconciliados. Foram conferidas cinco avaliações, snapshots, matrizes de confusão e precision/recall/F1; a implementação atual coincide com a v5 aceita. O CFR(b) foi recalculado por algoritmo independente (prefixos/searchsorted), sem chamar a função de produção. Os dados homologados e as hipóteses originais não foram alterados.

Há 350 unanimidades, 69 maiorias e uma resolução humana; zero pendências de consenso. A resolução de armbian/build permanece `no`, reviewer Islayder, com a justificativa humana original.

| Arquivo humano | SHA-256 confirmado |
|---|---|
| gold_sample_islayder.csv | `9cb894ee51a8cfde238dbd3e978064d4ccfc159812f94449b391342419811a51` |
| gold_sample_fernanda.csv | `f0b3bca6461306a6c3695538a152213b7991215610f200f17c29417625a00cfb` |
| gold_sample_vinicius.csv | `370fb02756ca4d10141a90857f60600885558fb4a975f6fd976edc3475d8eb9d` |

Consenso SHA-256: `db6f8bf9fe93c059a840491fa8b8de93195d1e6854391a6e0e3eaf23bb80f0e3`.

Kappa de Fleiss: tipo=0,862896; representatividade=0,154013; corretiva=0,735294. V5: TP83/FP36/FN27/TN154; precisão0,697479, recall0,754545, F1=0,724891. CFR(b) estável: 20.038 falhos, 6.406 não falhos, 677 censurados, 31 não avaliáveis; denominador26.444.

## 3. População, janela e completude — RQ01–04

Janela UTC `[2025-10-01, 2026-10-01)`, fim exclusivo, definida pelo grupo. A seleção S02 processou 1.782 candidatos e chegou aos mesmos 311 elegíveis. Não foi refeita na S03. A tabela usa estatísticas das métricas por repositório, não uma razão agregada de eventos.

| metric | unit | rq | n | missing | median | q1 | q3 | iqr | minimum | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| df | releases/week | RQ01 | 311 | 0 | 0.3260274 | 0.15342466 | 0.70958904 | 0.55616438 | 0.095890411 | 131.10137 |
| lt_release | hours | RQ02(a) | 261 | 50 | 179.66722 | 44.895417 | 526.76958 | 481.87417 | 0.0013888889 | 10488.387 |
| lt_commit | hours | RQ02(b) | 261 | 50 | 118.17028 | 27.719167 | 425.645 | 397.92583 | 0.0038888889 | 34592.488 |
| cfr_a | fraction | RQ03(a) | 311 | 0 | 0.052863436 | 0.021919289 | 0.11445964 | 0.092540351 | 0 | 0.83125 |
| cfr_b | fraction | RQ03(b) | 311 | 0 | 0.22727273 | 0.083333333 | 0.47169059 | 0.38835726 | 0 | 1 |
| recovery | hours | RQ04 | 286 | 25 | 3.3023611 | 0.83041667 | 18.797743 | 17.967326 | 0.013888889 | 2369.7819 |

Os 50 LT ausentes de referência são 29 erros de comparação e 21 de métrica. Recuperação: 23 sem episódios e dois somente censurados; 10.254 episódios, 114 censurados. Nenhum ausente foi transformado em zero.

## 4. DORA

| metric | category | n | valid | missing |
| --- | --- | --- | --- | --- |
| df | Low | 120 | 311 | 0 |
| df | Medium | 135 | 311 | 0 |
| df | High | 49 | 311 | 0 |
| df | Elite | 7 | 311 | 0 |
| lt_release | Low | 50 | 261 | 50 |
| lt_release | Medium | 86 | 261 | 50 |
| lt_release | High | 74 | 261 | 50 |
| lt_release | Elite | 51 | 261 | 50 |
| lt_commit | Low | 44 | 261 | 50 |
| lt_commit | Medium | 72 | 261 | 50 |
| lt_commit | High | 84 | 261 | 50 |
| lt_commit | Elite | 61 | 261 | 50 |
| cfr_a | Low | 8 | 311 | 0 |
| cfr_a | Medium | 13 | 311 | 0 |
| cfr_a | High | 36 | 311 | 0 |
| cfr_a | Elite | 254 | 311 | 0 |
| cfr_b | Low | 82 | 311 | 0 |
| cfr_b | Medium | 35 | 311 | 0 |
| cfr_b | High | 83 | 311 | 0 |
| cfr_b | Elite | 111 | 311 | 0 |
| recovery | Low | 14 | 286 | 25 |
| recovery | Medium | 40 | 286 | 25 |
| recovery | High | 151 | 286 | 25 |
| recovery | Elite | 81 | 286 | 25 |
| general | Low | 21 | 239 | 72 |
| general | Medium | 93 | 239 | 72 |
| general | High | 111 | 239 | 72 |
| general | Elite | 14 | 239 | 72 |

Geral C1 exige quatro valores: Low=1, Medium=2, High=3, Elite=4; piso da mediana. Há 239 válidos e 72 ausentes. Limites exatos estão na metodologia S03 e nos testes.

## 5. RQ05 — Spearman

| outcome | n | rho | p | p_permutation | permutations | seed | status | p_permutation_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| cfr_a | 311 | 0.063406025 | 0.26493747 | 0.2639 | 9999 | 42 | calculated | 0.2639 |
| cfr_b | 311 | 0.65137361 | 6.2039778e-39 | 0.0001 | 9999 | 42 | calculated | 0.0002 |

Associação DF×CFR(a) pequena e sem evidência ao nível de5%; DF×CFR(b) positiva expressiva. P de permutação usa9.999 trocas, seed42, Holm conjunto dos dois testes. O p assintótico de scipy.stats.spearmanr também está preservado. Não há inferência causal.

## 6. RQ06 — fatores e efeitos

| factor | metric | family | test | statistic | p | effect | effect_name | n | groups | status | p_holm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| stargazers_count | df | primary_12 | Kruskal–Wallis | 4.3458982 | 0.22645462 | 0.014019026 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.90581847 |
| stargazers_count | lt_release | primary_12 | Kruskal–Wallis | 4.1938046 | 0.2412829 | 0.016130018 | epsilon_squared_H_over_n_minus_1 | 261 | 4 | calculated | 0.90581847 |
| stargazers_count | cfr_a | primary_12 | Kruskal–Wallis | 5.40254 | 0.14458541 | 0.017427548 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.72292706 |
| stargazers_count | recovery | primary_12 | Kruskal–Wallis | 1.1405471 | 0.76729596 | 0.0040019196 | epsilon_squared_H_over_n_minus_1 | 286 | 4 | calculated | 1 |
| stargazers_count | cfr_b | supplementary_3 | Kruskal–Wallis | 2.5164346 | 0.4723283 | 0.008117531 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.4723283 |
| contributors_count | df | primary_12 | Kruskal–Wallis | 8.6533355 | 0.034273357 | 0.027913985 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.20564014 |
| contributors_count | lt_release | primary_12 | Kruskal–Wallis | 13.052729 | 0.0045239528 | 0.050202803 | epsilon_squared_H_over_n_minus_1 | 261 | 4 | calculated | 0.045239528 |
| contributors_count | cfr_a | primary_12 | Kruskal–Wallis | 0.25772933 | 0.96777198 | 0.00083138493 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 1 |
| contributors_count | recovery | primary_12 | Kruskal–Wallis | 11.978817 | 0.0074560777 | 0.042030937 | epsilon_squared_H_over_n_minus_1 | 286 | 4 | calculated | 0.059648621 |
| contributors_count | cfr_b | supplementary_3 | Kruskal–Wallis | 5.1494668 | 0.16117397 | 0.016611183 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.32234793 |
| repo_age_days | df | primary_12 | Kruskal–Wallis | 39.494012 | 1.363943e-08 | 0.12740004 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 1.5003373e-07 |
| repo_age_days | lt_release | primary_12 | Kruskal–Wallis | 43.563239 | 1.8685712e-09 | 0.16755092 | epsilon_squared_H_over_n_minus_1 | 261 | 4 | calculated | 2.2422854e-08 |
| repo_age_days | cfr_a | primary_12 | Kruskal–Wallis | 10.514176 | 0.014665038 | 0.033916698 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 0.10265526 |
| repo_age_days | recovery | primary_12 | Kruskal–Wallis | 12.799471 | 0.0050909541 | 0.044910423 | epsilon_squared_H_over_n_minus_1 | 286 | 4 | calculated | 0.045818587 |
| repo_age_days | cfr_b | supplementary_3 | Kruskal–Wallis | 47.886286 | 2.2514987e-10 | 0.15447189 | epsilon_squared_H_over_n_minus_1 | 311 | 4 | calculated | 6.7544962e-10 |

Família principal:12 testes, Holm conjunto; suplementar CFR(b):3 testes, outro Holm explícito. Todos os testes efetivos têm quatro grupos e usam Kruskal–Wallis. ε²=H/(n−1), conforme professor. O suporte Mann–Whitney/delta de Cliff está implementado e testado, sem inventar sua aplicação empírica. Cortes, n, medianas e IQR de cada grupo estão em factor_cutpoints.csv e factor_groups.csv. Não se identificam pares específicos pelo teste global.

## 7. RQ07 — definições distintas e coleta complementar

C1=estáveis/LT release/CFR(a); C2=estáveis+pré/LT commit/CFR(b); C3=tags/LT commit/CFR(a). Recuperação de CI é comum. Eventos:27.152/29.007/37.051. C3 usa data autoral do commit da tag. Coleta própria, APIs oficiais/cache/Git, sem PyGithub; somente contextos faltantes foram consultados. SHAs coincidentes permitem reutilizar um intervalo, nunca uma mediana de outra definição.

9.980 pares no plano complementar inicial, mais31 pares de fronteira. 622 verificações de primeira entrega (duas variantes×311):12 predecessoras de pré-release e240 de tags verificadas; cinco primeiras comparações de tags permaneceram indisponíveis por404. A ausência de predecessora observada não afirma ser a primeira entrega histórica. Planos/evidências anteriores estão preservados em data/raw/s03; snapshot offline versionado contém33.154 pares:20.084 exports exatos,3.059 SHAs idênticos,10.011 complementares. Estes têm7.399 completos,2.572 erros/ancestralidade inválida e40 compare404. Há um HTTP422 entre os erros.

LT C2:255 válidos/56 ausentes; C3:267/44. Entre os ausentes, C2 tem30 repos com duração negativa e35 com erro de comparação (nove em ambas as causas); C3 tem30/23, também com nove em ambas. C2/C3 não substituem resultados S02. C2 CFR:21.531 falhos,6.657 não falhos,784 censurados,35 não avaliáveis;193 classificações de contexto indisponível entre29.007 eventos.

| left | right | metric | n | changed | percent_changed | kappa_linear | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | C2 | df | 311 | 19 | 6.1093248 | 0.92557278 | calculated |
| C1 | C2 | lt | 255 | 121 | 47.45098 | 0.52065725 | calculated |
| C1 | C2 | cfr | 311 | 210 | 67.524116 | 0.015744525 | calculated |
| C1 | C2 | recovery | 286 | 0 | 0 | 1 | calculated |
| C1 | C2 | general | 233 | 85 | 36.480687 | 0.47515882 | calculated |
| C1 | C3 | df | 311 | 38 | 12.21865 | 0.84038419 | calculated |
| C1 | C3 | lt | 234 | 110 | 47.008547 | 0.51499449 | calculated |
| C1 | C3 | cfr | 311 | 0 | 0 | 1 | calculated |
| C1 | C3 | recovery | 286 | 0 | 0 | 1 | calculated |
| C1 | C3 | general | 213 | 55 | 25.821596 | 0.66941333 | calculated |
| C2 | C3 | df | 311 | 19 | 6.1093248 | 0.91264792 | calculated |
| C2 | C3 | lt | 231 | 17 | 7.3593074 | 0.93166513 | calculated |
| C2 | C3 | cfr | 311 | 210 | 67.524116 | 0.015744525 | calculated |
| C2 | C3 | recovery | 286 | 0 | 0 | 1 | calculated |
| C2 | C3 | general | 210 | 68 | 32.380952 | 0.55345912 | calculated |

Geral C2:233 válidos; C3:243. Os pares gerais usam233/213/210 casos. sensitivity_exclusions.csv enumera excluídos por par. As métricas iguais por construção (CFR(a) C1/C3 e recuperação) não comprovam validade das proxies.

### Interseção comum das três categorias gerais

| left | right | metric | n | changed | percent_changed | kappa_linear | status |
| --- | --- | --- | --- | --- | --- | --- | --- |
| C1 | C2 | general | 210 | 79 | 37.619048 | 0.45886371 | calculated |
| C1 | C3 | general | 210 | 54 | 25.714286 | 0.67268949 | calculated |
| C2 | C3 | general | 210 | 68 | 32.380952 | 0.55345912 | calculated |

## 8. Inovação — bootstrap de repositórios

| statistic | n | estimate | lower95 | upper95 | iterations | valid_replicates | seed | method | status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| median_df | 311 | 0.3260274 | 0.28767123 | 0.36438356 | 2000 | 2000 | 42 | repository_percentile_95 | calculated |
| median_cfr_a | 311 | 0.052863436 | 0.043299534 | 0.061145511 | 2000 | 2000 | 42 | repository_percentile_95 | calculated |
| median_cfr_b | 311 | 0.22727273 | 0.2 | 0.27272727 | 2000 | 2000 | 42 | repository_percentile_95 | calculated |
| rho_df_cfr_a | 311 | 0.063406025 | -0.051497743 | 0.179665 | 2000 | 2000 | 42 | repository_percentile_95 | calculated |
| rho_df_cfr_b | 311 | 0.65137361 | 0.57761815 | 0.71626471 | 2000 | 2000 | 42 | repository_percentile_95 | calculated |

2.000 réplicas, seed42; IC percentil95%; pares preservados nas correlações. Todas as cinco estimativas tiveram2.000 réplicas válidas. Precisão condicional às proxies/amostra, sem corrigir vieses de seleção ou da heurística.

## 9. RQ08 — retrabalho

| metric | unit | n | missing | median | q1 | q3 | iqr | minimum | maximum |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rework_rate | fraction | 274 | 37 | 0.42105263 | 0.2375817 | 0.6 | 0.3624183 | 0 | 1 |

274 taxas completas e37 ausentes; nestes37 casos reportam-se limites identificáveis, não ICs. As180 classificações desconhecidas não viram negativas. A razão conta corretivas, diferente dos originais de CFR(b).

## 10. Engenharia, execução e artefatos

Comando offline: `python -m src.s03`. Os scripts foram executados em dados reais;18 tabelas e27 arquivos de figura (nove figuras em PNG/SVG/PDF) foram reproduzidos byte a byte em duas pastas. Nenhuma credencial é necessária para reanalisar. `reproducibility.json` e `manifest.json` preservam a evidência, seeds, versões e hashes. A inspeção visual incluiu distribuições, dispersões, boxplots, ICs e transições; CFR(a/b) têm eixos de fração lineares comuns.

Artigo: article/metodologia_s03.md, resultados_s03.md, discussao_s03.md e ameacas_validade_s03.md. Os fragmentos S02 e introducao.md foram preservados. O material está organizado para integração futura ao SBC≤10p; não se declara paginação final de um artigo ainda não consolidado. README e docs/s03_analysis.md documentam execução, contratos e ausentes.

Suíte local: 583 testes, zero falhas/erros/skips; cobertura 96.96474434% (4153/4283 linhas), mínimo96% preservado. Ver test_summary.json; CI remoto em ci_s03.json. A organização posterior dos testes em arquivos de auditoria/sistema manteve as mesmas funções e passou no rerun focalizado.

## 11. Issues, commits, Projects e autoria

Issues reais #61–#73, com objetivos, critérios, dependências e artefatos. O estado remoto e fechamento técnico são atualizados após CI; #73 permanece pendente de ação humana. Os responsáveis não foram presumidos.

Commits de implementação auditados:

```text
da3b417 Integra analises offline e figuras reproduziveis (refs #69 #72)
375b38a Coleta intervalos e predecessoras reais da RQ07 (refs #66)
5dcd484 Implementa estatisticas DORA, inferencia e bootstrap (refs #62 #63 #64 #65 #67 #68)
bd4fcf1 Audita integridade S02 e registra processo da S03 (refs #61 #73)
```

Não foi criado outro Projects. A consulta retornou FORBIDDEN para a credencial; o board, WIP e seus estados não foram inventados. A atualização manual exata está em process.md/#73. A execução assistida centralizada não comprova contribuição individual de três integrantes; faltam divisão/revisões/commits de código efetivamente realizados por cada pessoa. Nenhuma autoria foi fabricada.

## 12. Conclusão sobre os requisitos

RQ01–RQ07, DORA, testes, artefatos reais, inovação e RQ08 estão implementados e executados, com faltantes e limitações rastreáveis. Permanecem pendências de processo: Projects e comprovação individual de código. A integração editorial final deve preservar hipóteses e contribuições e conferir paginação SBC. As limitações científicas remanescentes não foram escondidas: proxies, baixa concordância sobre entrega, validação interna v5, censuras, ausentes e comparação por conjuntos válidos. O CI/push são confirmados por SHA na evidência de publicação; a conclusão administrativa da sprint depende das ações humanas da #73.
