# Lab04 Final — Auditoria estatística e apresentação (Issue #84)

## Reprodução dos experimentos

O código em \`lab04/src/final_audit.py\` verifica que os resultados de Q1/Q2 incluem:
- pelo menos cinco tamanhos de efeito e um cenário de **efeito zero**;
- as mesmas condições experimentais (n, p₀, α, seed e 10.000 repetições por cenário);
- proporções de rejeição compatíveis com as contagens;
- efeitos em pontos percentuais corretamente calculados;
- erros padrão de Monte Carlo coerentes;
- ausência de duplicação de efeitos;
- reprodução opcional exata do CSV pela seed e pelos parâmetros.

Execute na raiz, após instalar `lab04/requirements.txt`.

```bash
python -m pytest -q lab04/tests
python -m lab04.src.final_audit --replay
python -m lab04.src.final_audit --replay --csv lab04/results/s02_q3.csv
```

Os dois replays reproduzem seis efeitos cada, com 10.000 repetições por
efeito e semente 42. Para a checagem independente da amostra real,
conte `failure` na coluna `conclusion` e confira o indicador `failed`.
São 169 IDs distintos e sete falhas. Com n e k, o p-valor exato é a
soma das massas binomiais de k a n em p₀ = 0,05. A cauda normal no Z
resulta em 0,6956 e a soma binomial em 0,7452.

Em Python 3.13.15, passaram **116 testes do Lab04** e **249 testes** na
suíte global com as dependências de métricas do Lab02 instaladas. O smoke
test confirma a ordem das sete seções. O teste de interação altera os
controles de G2 e compara as tabelas oficiais antes e depois.

## Rastreabilidade

Os quatro PRs históricos já têm seus commits em `Laboratorio-4`.

| PR | Base no GitHub | Commit | Situação para o Lab04 |
|---|---|---|---|
| [#80](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/pull/80) | `main` | `150c1fe` | Fechado sem merge; código preservado na branch oficial |
| [#87](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/pull/87) | `main` | `150c1fe` | Aberto; redundante para a branch oficial |
| [#88](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/pull/88) | `lab04-s01-recovered` | `007847e` | Aberto; redundante para a branch oficial |
| [#89](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/pull/89) | `lab04-s02-islayder` | `c75fcd5` | Aberto; redundante para a branch oficial |

| Issue | Evidência e aceite técnico |
|---|---|
| #77 | `ddc8a89` · origem, exclusões, IDs e contagem conferidos no snapshot e nos testes |
| #78 | `150c1fe` · testes unitários, mesma amostra e exemplo S01 reproduzido |
| #79 | `df8c048`, `cab3840` · G1/G2 renderizados e separados por fonte |
| #81 | `007847e` · seis efeitos, 10.000 repetições e replay de Q1/Q2 |
| #82 | `d2ccd19` · Q3 compara erro tipo I e poder com a referência, com replay e limiares teóricos |
| #83 | `68aeaee` · G3/G4 renderizados, testados contra as tabelas e comparados a 5% |
| #84 | `c75fcd5` e PR final · auditoria, testes de integração e roteiro oral abaixo |
| #85 | `bde91b5` e PR final · tabela real conferida, conclusão e [roteiro de Fernanda](apresentacao_fernanda.md) |
| #86 | `38c1012` e PR final · sete seções, legendas, navegação, revisão visual local e [instruções de deploy](../README.md#publicação-no-streamlit-community-cloud) |

O aceite em revisão, a publicação e o ensaio da apresentação de até sete
minutos dependem do grupo. As Issues e os PRs históricos foram consultados.

## Respostas de Islayder — perguntas 2, 5, 7, 8 e 12

**2. Unicaudal ou bicaudal?** Unicaudal à direita: investigamos se p > 0,05, não qualquer diferença em relação a 5%.

**5. O que os testes comparam?** Os dois avaliam a quantidade/proporção de falhas frente a uma taxa de referência de 5%. O Z aproxima sua estatística pela normal; o binomial exato usa a probabilidade discreta exata sob H₀. Ambos trabalham na fronteira p₀ = 0,05.

**7. O que significa p-valor?** É a probabilidade, **sob a hipótese nula na fronteira p=5%**, de observar resultado tão extremo ou mais extremo na direção de H₁. Não é a probabilidade de H₀ estar certa ou errada e não mede o tamanho do efeito.

**8. Erros tipo I e II?** Tipo I: indicar uma taxa acima de 5% quando ela na verdade não excede esse valor (falso alarme). Tipo II: deixar de detectar que a taxa real excede 5% (falha que passa despercebida). Num CI, consideramos o tipo II potencialmente mais grave por deixar um problema real sem investigação; a prioridade pode mudar conforme o custo de cada erro.

**12. Se α baixar de 0,05 para 0,01?** A região de rejeição fica mais exigente. Em geral, **erro tipo I cai e poder também cai**, se tamanho amostral e efeito permanecerem iguais; o risco de tipo II cresce. É preciso reexecutar/avaliar os dois testes com α=0,01, não reaproveitar as mesmas taxas de rejeição.

Todos devem conhecer as 15 perguntas: a divisão é para organização, não limita a arguição do professor.
