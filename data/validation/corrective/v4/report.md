# #58 — heurística v4

Mesma maioria estrita de v3 entre mudanças funcionais: exclui seções de dependências, documentação e mudanças internas, assuntos explicitamente tipados como manutenção/refactor e entradas administrativas de release. Remove prefixos de SHA antes de identificar o tipo. Mantém mudanças funcionais desconhecidas no denominador e não usa patch isolado.

300 releases; precisão 0.8636; recall 0.5182; F1 0.6477.

Status: needs_refinement. Limiar: 0,70 (comparação sem arredondamento).

TP=57; FP=9; FN=53; TN=181.
Contexto de commits incompleto: 11.

Confira no JSON os casos de métricas indefinidas. F1 abaixo de 0,70 exige refinamento e nova avaliação.
Preserve esta pasta; não escolha uma versão pela acurácia nem substitua o consenso pelos votos de uma pessoa.
