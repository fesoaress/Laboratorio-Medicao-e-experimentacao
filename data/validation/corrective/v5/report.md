# #58 — heurística v5

Refinamento lexical de v2: reconhece adições, introduções, suporte e melhorias como sinais funcionais concorrentes às correções; ignora manutenção explicitamente tipada e seções administrativas. Compara correções contra sinais funcionais nas notas; na ausência de sinais usa commits. Empate é negativo; patch isolado não classifica.

300 releases; precisão 0.6975; recall 0.7545; F1 0.7249.

Status: accepted. Limiar: 0,70 (comparação sem arredondamento).

TP=83; FP=36; FN=27; TN=154.
Contexto de commits incompleto: 11.

Confira no JSON os casos de métricas indefinidas. F1 abaixo de 0,70 exige refinamento e nova avaliação.
Preserve esta pasta; não escolha uma versão pela acurácia nem substitua o consenso pelos votos de uma pessoa.
