# Lab02 S03 — contribuição individual de Islayder

**Issue:** #33 — RQ1, RQ2 e inovação.  
**Responsabilidade:** auditar os dados da S02, analisar tempo, testes e
evolução por ciclo; gerar artefatos reproduzíveis; redigir a parte
correspondente do relatório-base do grupo.

## Trabalho realizado

- Criado `lab02/analysis/analyze_rq1_rq2.py`, executável da raiz do
  repositório, com leitura dos dois CSVs oficiais, auditoria de esquema,
  chaves, proveniência, matriz de participante/kata/tratamento, Issue,
  contagens de testes, tempo, censura e ciclos.
- Segregados os quatro cenários `observed_simulated` de Islayder; as duas
  tentativas inválidas de Vinicius e os quatro ensaios do instrumento de
  Fernanda foram excluídos com justificativa e ID auditáveis. Dados
  brutos não foram alterados.
- RQ1: calculados mediana, Q1, Q3 e IQR por tratamento; preservado o
  detalhe por kata. Documentada a impossibilidade de Wilcoxon pareado:
  apenas um participante completo e elegível.
- RQ2: comparados passed/failed, taxa de sucesso e status final, sem
  inferência indevida sobre contagens absolutas de katas diferentes.
- Inovação: medidos ciclos, taxas no primeiro e último ciclo, tempo de
  cada ciclo e ciclo até green; identificada a limitação de três trials
  com apenas um ciclo.
- Preparado o relatório-base do grupo com seções completas de RQ1/RQ2/
  inovação e espaços explícitos para RQ3 de Fernanda e dashboard de Vinicius.

## Resultados principais

Os quatro trials válidos são de Vinicius (dois IA e dois Manual), todos
green, sem censura válida. A mediana do tempo foi **3,121 min IA** e
**6,814 min Manual**; IQR **2,288 min IA** e **0,715 min Manual**.
Wilcoxon: **não aplicado**, W e valor-p não aplicáveis, **n efetivo = 1
par de participante**. Em RQ2, ambos os tratamentos terminaram com
100% de testes passando (IA 19/19, Manual 16/16) e zero falhas finais.
Na inovação, IA chegou ao green no ciclo 1 em ambos os trials; Manual
chegou nos ciclos 1 e 2, sendo K4 Manual o único com mudança registrada
entre ciclos (0% → 100%). Essas diferenças são somente descritivas.

## Artefatos

- [Script e regras](../../../lab02/analysis/analyze_rq1_rq2.py) e
  [instruções de reprodução](../../../lab02/analysis/README.md).
- [Tabelas e auditoria](../../../lab02/analysis/results/auditoria_trials.csv),
  com os demais CSVs em `lab02/analysis/results/`.
- [Tempo IA × Manual](../../figures/rq1_tempo_ia_vs_manual.png),
  [testes IA × Manual](../../figures/rq2_testes_ia_vs_manual.png),
  [evolução dos testes](../../figures/inovacao_evolucao_testes.png) e
  [ciclos até green](../../figures/inovacao_ciclos_ate_green.png).
- [Relatório-base S03](relatorio_s03.md).

## Validação

O script foi executado integralmente e os 12 artefatos gerados (8 CSVs e
4 PNGs) mantiveram hashes idênticos em duas execuções consecutivas.
Uma conferência independente verificou as 14 linhas auditadas, as quatro
incluídas, medianas, IQRs, totais de testes e presença dos gráficos. Os
links locais dos relatórios foram resolvidos. A suíte existente de trials,
métricas e simulação passou com **24 testes** após instalar as dependências
declaradas; `python -m compileall lab02` e `git diff --check` passaram.

## Limitações e pendências externas

Islayder não possui execução humana S02 registrada; os quatro registros
associados ao nome são simulações. Os quatro de Fernanda estão como
`observed`, mas seu relatório S02 os classifica como ensaio inválido para
tempo de resolução. Assim, só um participante pode ser analisado. O
contrabalanceamento planejado não se realiza na amostra elegível; os
katas IA e Manual são diferentes. Não se afirma significância nem efeito
causal. A conclusão global aguarda dados válidos adicionais, RQ3 de
Fernanda (#34) e dashboard de Vinicius (#35).
