# #58 — heurística v2

Predominância de correções sobre features nas notas; na ausência de sinais nas notas, nos commits. Ignora commits de manutenção explicitamente tipados; empate é negativo. Patch SemVer é fallback somente quando não há sinais de correção/feature.

300 releases; precisão 0.4796; recall 0.9636; F1 0.6405.

Status: needs_refinement. Limiar: 0,70 (comparação sem arredondamento).

TP=106; FP=115; FN=4; TN=75.
Contexto de commits incompleto: 11.

Confira no JSON os casos de métricas indefinidas. F1 abaixo de 0,70 exige refinamento e nova avaliação.
Preserve esta pasta; não escolha uma versão pela acurácia nem substitua o consenso pelos votos de uma pessoa.
