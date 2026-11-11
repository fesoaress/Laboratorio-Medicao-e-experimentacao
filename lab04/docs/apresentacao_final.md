# Lab04 — Apresentação final e defesa

Roteiro de apresentação contínua, seguindo as **sete seções do dashboard** e as **15 perguntas de defesa**. Este documento substitui a divisão anterior: **Islayder: 1–5; Vinicius: 6–10; Fernanda: 11–15**. A divisão organiza a fala, mas **todos devem saber responder às 15 perguntas**.

**Dashboard:** https://lab04-medicao-pucminas.streamlit.app/  
**Branch:** Laboratorio-4  
**Parâmetros oficiais:** H₀: p ≤ 0,05; H₁: p > 0,05; α = 0,05.  
**Tempo:** aproximadamente 6min40s de fala e 20s para transições, dentro do limite de sete minutos.

## Navegação e divisão

| Tempo sugerido | Quem | Perguntas | O que estará visível |
|---|---|---|---|
| 0:00–2:20 | **Islayder** | 1–5 | Seção 1 (cenário), seção 2 (**G1**), seção 3 (**G2**, introdução) |
| 2:20–4:35 | **Vinicius** | 6–10 | Continuação de **G2**, seção 4 (**G3**) e seção 5 (**G4**) |
| 4:35–6:40 | **Fernanda** | 11–15 | **G4** para pressupostos, seção 6 (dados reais) e seção 7 (conclusão) |
| 6:40–7:00 | Grupo | — | Margem de tempo / fechamento |

**Antes de começar:** manter os controles de G1/G2 nos valores iniciais (n = 30, probabilidade hipotética de falha de 10%, semente 42, p₀ = 5% e α = 5%). G3/G4 são resultados oficiais fixos de 10.000 repetições por cenário: os controles da barra lateral **não os recalculam**.

O texto abaixo é para ser **falado naturalmente**, sem anunciar os números das perguntas. A tabela e as respostas de defesa servem para garantir a cobertura.

## Fala 1 — Islayder (1–5)

### Tela: seção 1 — Cenário

> Boa noite! Nosso estudo compara dois testes de hipótese para entender quando cada um é mais adequado.
>
> Avaliamos a taxa de falhas de execuções concluídas de integração contínua, ou CI, diante de uma meta de no máximo 5%. H₀ afirma que a taxa é menor ou igual a 5%, e H₁, que é maior. Portanto, usamos testes unilaterais à direita: só queremos detectar quando a taxa ultrapassa a meta.

### Tela: seção 2 — G1, três painéis

> Coletamos 169 execuções do GitHub Actions do FastAPI: 162 sucessos e sete falhas, ou 4,14% de falhas. Cada execução tem resultado binário, modelado por Bernoulli.
>
> No G1, vemos os dados reais e duas amostras simuladas, de 30 e 200 execuções. Escolhemos 200 por ser próximo dos 169 dados reais e 30 para avaliar uma amostra pequena. Uma falha representa 3,33 pontos percentuais em 30 execuções, mas só 0,5 em 200. Esse é o motivo para investigar o efeito do tamanho amostral.
>
> As duas simulações visíveis são exemplos com probabilidade hipotética de falha de 10%; não são as 10.000 repetições oficiais, analisadas nos próximos gráficos.

### Tela: seção 3 — G2, introdução

> No G2, os dois testes avaliam a mesma proporção de falhas contra 5%. Acima, cada barra do binomial exato representa a probabilidade de uma contagem de falhas. Abaixo, o Z usa uma aproximação normal, aquela curva em sino.
>
> As caudas coloridas mostram os p-valores e as áreas hachuradas indicam as regiões de rejeição. O Vinicius vai aprofundar essa diferença e mostrar o que aconteceu nos experimentos.

**Na tela:** apontar para **169 → 30 → 200** e, no G2, **barras → curva**. O G1 é uma ilustração; não usar amostras individuais para afirmar que o Z é pior.

## Fala 2 — Vinicius (6–10)

### Tela: seção 3 — G2, aprofundamento

> Sob a fronteira de H₀, a taxa é 5%. O binomial exato calcula a cauda de uma contagem binomial; o Z aproxima essa probabilidade pela normal.
>
> Como o teste é à direita, procuramos contagens altas. Com 30 execuções e α de 5%, o Z rejeita a partir de quatro falhas, e o exato só a partir de cinco. Assim, podem tomar decisões diferentes.
>
> O p-valor é a probabilidade, supondo H₀ na fronteira, de obter um resultado pelo menos tão extremo quanto o observado; não é a chance de H₀ estar correta.
>
> Erro tipo I é dar um falso alarme quando a taxa não supera 5%. Erro tipo II é não detectar quando supera. No CI, ambos têm custos, entre investigações desnecessárias e falhas ignoradas.

### Tela: seção 4 — G3

> O G3 mede falsos alarmes sob H₀. Com 30 execuções, o Z teve 6,05%, acima do α de 5%, e foi liberal; o binomial exato teve 1,69%, sendo conservador. Com 200, ambos tiveram 4,48%.

### Tela: seção 5 — G4

> O G4 mostra poder, isto é, a capacidade de detectar uma taxa acima da meta. Com 30 execuções e taxa verdadeira de 10%, o Z teve 35,89% e o exato 17,53%. Mas o Z também gerou falsos alarmes demais, como vimos no G3. Com 200 execuções, as curvas coincidiram nos cenários estudados.
>
> A Fernanda conclui explicando essa diferença e os resultados observados no FastAPI.

**Na tela:** G2 para p-valores/limiares; G3 para **6,05% versus 1,69%**; G4 para o ponto de **efeito +5 p.p.** em **n = 30**. Maior poder sozinho não torna o Z superior.

## Fala 3 — Fernanda (11–15)

### Tela: seção 5 — G4, relacionando com G3

> Por que houve diferença? Sob H₀, com 30 execuções esperamos só 1,5 falha. Essa quantidade pequena torna a aproximação normal pouco adequada. Com 200 execuções, esperamos dez falhas, e os testes concordaram nas condições estudadas.
>
> Se diminuíssemos α para 1%, ficaria mais difícil rejeitar H₀, então tanto o erro tipo I quanto o poder não aumentariam. Isso é uma consequência teórica; G3 e G4 não foram recalculados para α de 1%.

### Tela: seção 6 — Dados reais

> Nos dados reais, foram sete falhas em 169 execuções, uma taxa de 4,14%. O p-valor do Z foi 0,6956 e o do binomial exato 0,7452. Nenhum rejeitou H₀. Portanto, não há evidência suficiente de que a taxa excede 5%, mas isso não prova que a meta esteja garantida.
>
> O efeito observado foi de −0,86 ponto percentual em relação à meta, indicando uma diferença pequena e para baixo.

### Tela: seção 7 — Conclusão

> A expectativa era de maior dificuldade para o Z com poucas falhas esperadas, e a simulação confirmou isso em n = 30. Em n = 200, ambos concordaram nos cenários analisados.
>
> Recomendamos o binomial exato com falhas raras e amostras pequenas. O Z é uma opção quando há mais falhas e sucessos esperados. A limitação é que supomos independência e probabilidade de falha constante; na prática, execuções de CI podem compartilhar causas. Também observamos só um workflow em um período.

**Na tela:** G4/G3 para o pressuposto; seção 6 para **p-valores e −0,86 p.p.**; seção 7 para **expectativa, recomendação e limitações**. A discussão de α = 1% é qualitativa: a seção 3 permite explorar α no G2, **não** recalcula G3/G4.

## Cobertura das 15 perguntas e apoio visual

| Pergunta | Responsável | Onde mostrar | Ponto que deve ficar claro |
|---|---|---|---|
| 1. Cenário, H₀ e H₁ | Islayder | Seção 1 | Taxa de falhas e meta de 5% |
| 2. Unilateral ou bilateral? | Islayder | Seção 1 | À direita porque H₁ é p > 5% |
| 3. Coleta e formato da distribuição real | Islayder | Seção 1 e G1 | 169 execuções, 162 sucessos e 7 falhas; Bernoulli |
| 4. Escolha dos parâmetros | Islayder | G1 e justificativa aberta | n = 200 próximo dos reais; n = 30 como amostra pequena; p₀ = 5% |
| 5. O que os testes comparam? | Islayder | G2 | Mesma proporção, cálculo normal versus binomial |
| 6. Distribuições e rejeição | Vinicius | G2 | Binomial discreta / Z normal e caudas à direita |
| 7. Interpretação do p-valor | Vinicius | G2 e métricas | Probabilidade condicional sob H₀, não P(H₀ verdadeira) |
| 8. Erro tipo I/II e gravidade | Vinicius | G3 e G4 | Falso alarme versus falha em detectar |
| 9. Liberal/conservador | Vinicius | G3 | n = 30: Z 6,05%; exato 1,69% |
| 10. Poder e efeito | Vinicius | G4 | Com n = 30, mais rejeições do Z vêm com maior erro tipo I |
| 11. Pressuposto e impacto | Fernanda | G4 / texto de conclusão Q3 | n × p₀ = 1,5 prejudica aproximação normal |
| 12. α = 1% | Fernanda | Controle de α no G2 (referência conceitual) | Explicar a direção; não inventar números de G3/G4 |
| 13. Expectativa inicial | Fernanda | Seção 7 | Divergência em n = 30; coincidência em n = 200 |
| 14. Resultado real e efeito | Fernanda | Seção 6 | p-valores, não rejeição, −0,86 p.p. |
| 15. Recomendação e limitações | Fernanda | Seção 7 | Exato com poucas falhas; independência e p constante |

## Respostas de defesa — caso o professor aprofunde

**1–2 (Islayder).** H₀: p ≤ 5%; H₁: p > 5%. Unilateral à direita porque só buscamos evidência de que a taxa ultrapassa a meta.

**3 (Islayder).** API pública do GitHub Actions, workflow Test de fastapi/fastapi, pushes na branch master, de 01/07 a 30/09/2026 UTC. Foram incluídos 162 sucessos e sete falhas; oito cancelamentos foram excluídos. Cada execução tem desfecho binário (Bernoulli); sob independência e p constante, K é binomial.

**4 (Islayder).** n real = 169 orientou n = 200. n = 30 é o cenário de estresse para a aproximação. A meta p₀ = 5% vem da pergunta de pesquisa; os cenários oficiais usam p verdadeiro de 5% a 20%. Os 10% de G1 são somente um exemplo exploratório.

**5 (Islayder).** Os dois testes avaliam a proporção de falhas contra p₀ usando a mesma contagem K e tamanho n. O Z padroniza a diferença de proporções e usa a normal; o exato calcula P(K ≥ k) sob Bin(n,p₀).

**6 (Vinicius).** Na fronteira de H₀, K ∼ Bin(n,0,05); o Z usa aproximadamente N(0,1). Em n = 30, α = 5%, Z rejeita a partir de K = 4 e exato a partir de K = 5.

**7 (Vinicius).** p-valor é a probabilidade de estatística tão extrema quanto a observada ou mais, na direção da hipótese alternativa, **calculada supondo H₀ na fronteira**. Não mede a probabilidade de a hipótese ser verdadeira.

**8 (Vinicius).** Tipo I: falso alarme quando p ≤ 5%. Tipo II: não detectar p > 5%. O custo relativo depende das consequências operacionais, como investigação desnecessária ou demora na correção.

**9 (Vinicius).** Em n = 30, Z liberal (6,05%) e exato conservador (1,69%). Em n = 200, ambos tiveram 4,48% no experimento.

**10 (Vinicius).** O poder aumenta com o efeito. Com n = 30 e p = 10%, Z 35,89%, exato 17,53%, mas Z excedeu o erro tipo I nominal. Com n = 200, curvas coincidiram nos efeitos estudados.

**11 (Fernanda).** Com n = 30, n p₀ = 1,5 falha esperada, violando a condição prática de boa aproximação normal. Para n = 200, n p₀ = 10, e ambos rejeitam a partir de 16 falhas neste cenário.

**12 (Fernanda).** Diminuir α para 1% deixa a região crítica menor ou igual. Para mesmo n e p, erro tipo I e poder não aumentam. Sem recalcular as simulações, não afirmar taxas numéricas para α = 1%.

**13 (Fernanda).** A expectativa da S01 se confirmou nas condições examinadas: divergência com n = 30 e concordância com n = 200.

**14 (Fernanda).** 7/169 = 4,14%, Z = −0,512 (p = 0,6956), binomial K = 7 (p = 0,7452). Evidência insuficiente para p > 5%, não prova de conformidade. Efeito observado: −0,86 p.p.

**15 (Fernanda).** Prefira o exato com falhas raras e poucas falhas esperadas; o Z pode funcionar bem com contagens maiores. Limitações: independência, p constante e escopo de um workflow/período.

## Checklist do ensaio

- **Mostrar, não só dizer:** cada integrante aponta a seção/figura/valor no momento em que faz a afirmação. Evitar ler as 15 perguntas como um questionário.
- **G1:** conferir três painéis atualizados; real n = 169, simulados n = 30 e n = 200. **Não confundir** as amostras individuais com as 10.000 repetições oficiais.
- **G2:** manter o valor n = 30 do exemplo. Nunca insinuar que alterar α no G2 atualiza G3/G4.
- **G3/G4:** mostrar o contraste entre erro tipo I e poder, sem concluir que o Z é sempre melhor porque rejeitou mais.
- **Seções 6/7:** mostrar valores de p e efeito, a expectativa inicial, a recomendação e as limitações.
- **Cronometrar:** adequar a quantidade de palavras ao ritmo real e preservar a margem de 20 segundos.
- **Antes de entregar:** conferir GitHub Projects e o link público do Streamlit; o roteiro não substitui a validação da aplicação.
