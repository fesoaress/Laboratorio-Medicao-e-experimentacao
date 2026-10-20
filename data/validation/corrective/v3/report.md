# #58 — heurística v3

Maioria estrita de entradas corretivas entre TODAS as mudanças nas notas; listas de contribuidores, links de changelog e blocos de código não são mudanças. Sem entradas nas notas, usa maioria estrita de assuntos de commits não tipados como manutenção/merge. Notas com mudanças têm precedência; patch SemVer isolado não é evidência suficiente.

300 releases; precisão 0.9057; recall 0.4364; F1 0.5890.

Status: needs_refinement. Limiar: 0,70 (comparação sem arredondamento).

TP=48; FP=5; FN=62; TN=185.
Contexto de commits incompleto: 11.

Confira no JSON os casos de métricas indefinidas. F1 abaixo de 0,70 exige refinamento e nova avaliação.
Preserve esta pasta; não escolha uma versão pela acurácia nem substitua o consenso pelos votos de uma pessoa.
