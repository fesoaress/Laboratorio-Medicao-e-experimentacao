# Lab04 — preparação de Fernanda para a apresentação (#85)

Este roteiro cobre as cinco perguntas atribuídas no grupo. Os números vêm de
`lab04/data/ci_runs.csv`, `lab04/results/s02_q1_q2.csv` e
`lab04/results/s02_q3.csv`; o dashboard calcula os testes reais em
`lab04/src/real_results.py`. Todos os integrantes devem conhecer também as
outras perguntas da arguição.

## 1. Qual é o cenário e quais são H₀ e H₁?

> Investigamos se a taxa de falha das execuções concluídas do workflow **Test**
> do FastAPI ultrapassa **5%**. A hipótese nula é **H₀: p ≤ 0,05** e a alternativa
> é **H₁: p > 0,05**. Por isso os testes são unilaterais à direita, com
> **α=0,05**: só uma proporção suficientemente alta de falhas levaria à
> rejeição de H₀.

## 3. Como coletamos os dados e qual é a distribuição?

> Consultamos a API pública do GitHub Actions para o mesmo workflow, branch
> `master` e evento `push`, de **1º de julho a 30 de setembro de 2026**, em
> UTC. Incluímos somente conclusões `success` e `failure`; oito execuções
> `cancelled` ficaram fora do denominador. Obtivemos **169 execuções válidas**:
> **162 sucessos e sete falhas**, ou **4,14%** de falhas. Cada resultado é 0 ou
> 1; sob a simplificação de ensaios independentes com p constante, a contagem
> de falhas em n execuções segue uma Binomial(n,p). O G1 mostra as contagens,
> não uma distribuição normal dos resultados individuais.

Fonte verificável: `lab04/docs/cenario_s01.md` e as URLs de execução em cada
linha de `lab04/data/ci_runs.csv`.

## 4. Como os dados reais definiram os parâmetros da simulação?

> Os dados reais mostraram que a variável é binária e que o tamanho observado
> é **n=169**. O grupo usou **n=200** como referência de amostra maior e
> **n=30** como situação crítica; esses são tamanhos de cenário, não novas
> coletas. A meta **p₀=5%** vem da pergunta de pesquisa, e a taxa empírica
> **p̂=4,14%** apenas descreve a amostra: ela não substitui p₀. Para estimar
> erro tipo I simulamos p_real=5%; para poder escolhemos probabilidades
> hipotéticas acima de 5%, de 7,5% a 20%, com **10.000 repetições por ponto**
> e semente 42. Nenhuma execução real foi inserida nas amostras simuladas.

## 11. Qual pressuposto foi problemático e qual foi o efeito?

> No cenário de **n=30** e **p₀=5%**, o número esperado de falhas sob H₀ é
> **n·p₀=1,5**, abaixo da regra prática de cinco para a aproximação normal
> do Z. O binomial exato continua aplicável ao modelo Binomial. Sob H₀, o Z
> rejeitou **6,05%** das vezes, acima de α, e o exato rejeitou **1,69%**.
> O Z já rejeita com **quatro** falhas; o exato requer **cinco**. Em n=200,
> n·p₀=10 e ambos rejeitam a partir de 16 falhas; na simulação, ambos
> rejeitaram **4,48%** das vezes. A preocupação é com a aproximação da
> contagem discreta por uma normal, não com a raridade isolada da falha.

## 14. Qual foi a conclusão real e por que importa o tamanho do efeito?

> Nos dados reais, **sete falhas em 169 execuções** dão **4,14%**. O Z foi
> **−0,512**, com **p=0,6956**; o binomial exato teve **K=7** e **p=0,7452**.
> Com α=0,05, **nenhum rejeita H₀**: não há evidência nesta amostra de taxa
> acima de 5%, mas isso não prova que a taxa verdadeira esteja abaixo da meta.
> A diferença observada **p̂−p₀ é −0,86 ponto percentual** (magnitude
> 0,86 p.p.), pequena em relação à referência. O p-valor informa sobre a
> decisão estatística; a diferença em pontos percentuais ajuda a avaliar a
> importância prática. Para falhas raras e amostras pequenas, recomendamos o
> binomial exato porque não depende da aproximação normal; os dois testes
> concordaram na amostra real.

## Limite que vale mencionar se perguntarem

A amostra veio de um único workflow e período. Execuções próximas podem
compartilhar commits e causas de falha, de modo que independência e
probabilidade constante são simplificações do modelo. O resultado não mede
falhas de produção nem representa todos os projetos do GitHub.

## Revisão rápida das outras dez perguntas

As Issues #84 e #86 distribuem a fala principal dessas perguntas aos colegas,
mas a arguição pode ser dirigida a qualquer integrante.

- **2 — Por que unilateral?** H₁ pergunta somente se p **ultrapassa** 5%,
  não se há qualquer diferença para 5%; a rejeição fica na cauda direita.
- **5 — O que os testes comparam?** Ambos comparam o mesmo n e k com p₀=5%.
  O Z usa uma aproximação normal; o exato calcula a cauda da Binomial.
- **6 — Distribuição e região em G2:** sob H₀ na fronteira, K segue
  Binomial(n,0,05) e Z é aproximado por N(0,1). Rejeitamos para contagens
  altas; em n=30, o limiar é K≥4 no Z e K≥5 no exato.
- **7 — O que é p-valor?** É a probabilidade, **supondo H₀ na fronteira**,
  de observar um resultado pelo menos tão extremo na direção de H₁. Não é
  a probabilidade de H₀ estar correta nem o tamanho do efeito.
- **8 — Erros tipo I e II:** tipo I é alarme falso de taxa acima da meta;
  tipo II é deixar passar uma taxa realmente acima da meta. A gravidade
  relativa depende do custo de investigar falsos alarmes e do custo de não
  detectar falhas reais de CI.
- **9 — Quem foi liberal/conservador em G3?** Em n=30, Z=6,05% foi liberal
  e exato=1,69% foi conservador. Em n=200, ambos=4,48%, ligeiramente
  conservadores no cenário simulado.
- **10 — Quem teve mais poder em G4?** Em n=30, o Z rejeitou mais em todos
  os efeitos positivos, mas também excedeu α sob H₀. Em n=200, as curvas
  coincidiram neste desenho. Poder cresce conforme p_real se afasta de 5%.
- **12 — E se α cair para 1%?** O limiar de rejeição fica mais exigente:
  geralmente caem erro tipo I e poder. É preciso recalcular G3/G4 para
  α=1%; não se reaproveitam as taxas produzidas com α=5%.
- **13 — A expectativa foi confirmada?** Sim quanto à divergência em n=30
  e à coincidência em n=200 neste cenário. Isso é uma conclusão sobre os
  parâmetros simulados, não uma regra universal para qualquer n e p.
- **15 — Qual teste recomendar?** O binomial exato para o cenário de falhas
  raras, sobretudo quando n·p₀ é pequeno. O Z pode ser uma aproximação útil
  com contagens esperadas maiores; se as execuções forem dependentes, a
  calibração de ambos exige cuidado adicional.
