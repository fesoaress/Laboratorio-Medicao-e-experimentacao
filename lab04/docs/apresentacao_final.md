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

> Boa noite! Nosso estudo compara dois testes de hipótese para entender como eles se comportam e em quais situações usar cada um.
>
> Nosso cenário é avaliar a taxa de falhas de um processo de integração contínua, o CI. A meta considerada é de, no máximo, 5% de falhas.
>
> Nossa hipótese nula, H₀, afirma que a taxa é menor ou igual a 5%, enquanto H₁ afirma que ela é maior que 5%. Portanto, os testes são unilaterais à direita: queremos investigar especificamente se a taxa ultrapassa essa meta.

### Tela: seção 2 — G1, agora com três painéis

> Coletamos 169 execuções concluídas do GitHub Actions do projeto FastAPI, com 162 sucessos e sete falhas. Foram consideradas somente execuções com resultado sucesso ou falha. Como cada execução tem dois resultados possíveis, podemos representá-la como uma variável de Bernoulli. Observamos 4,14% de falhas, com concentração de sucessos.
>
> No G1, vemos três painéis: os 169 dados reais e duas amostras simuladas, com 30 e 200 execuções. A comparação mostra por que o tamanho importa: com 30 execuções, uma única falha muda a proporção muito mais do que com 200.
>
> O tamanho 200 foi escolhido por ser próximo das 169 execuções reais; o tamanho 30 permite investigar uma situação com poucas falhas esperadas. As amostras do G1 são exemplos individuais, inicialmente com probabilidade hipotética de falha de 10%. Os resultados oficiais, com 10.000 repetições por cenário e probabilidades de 5% a 20%, aparecem em G3 e G4.

### Tela: seção 3 — G2, abertura

> No G2, comparamos como os dois testes analisam a **mesma proporção de falhas** em relação à meta de 5%. No gráfico superior, o binomial exato trabalha diretamente com a contagem de falhas; cada barra representa uma quantidade possível. No inferior, o teste Z usa uma aproximação normal, mostrada pela curva.
>
> As áreas coloridas mostram as caudas associadas aos p-valores, e as áreas hachuradas mostram onde rejeitaríamos H₀. O Vinicius vai explicar como essas regiões são definidas e o que observamos nas simulações.

**Ponte visual:** no G1 apontar para **169 → 30 → 200**; no G2 apontar **barras superiores → curva inferior**. Não afirmar que o G1, por si só, demonstra que o teste Z é pior.

## Fala 2 — Vinicius (6–10)

### Tela: seção 3 — G2, aprofundamento

> Sob a fronteira da hipótese nula, usamos p = 5%. No binomial exato, a quantidade K de falhas segue uma distribuição binomial. No Z, a referência é a distribuição normal padrão, usada como aproximação.
>
> Como queremos detectar taxas acima da meta, as regiões de rejeição estão à direita. Com n = 30 e α = 5%, o Z começa a rejeitar quando aparecem quatro falhas; o binomial exato exige pelo menos cinco.
>
> O p-valor indica, supondo a taxa de 5%, a probabilidade de um resultado tão extremo quanto o observado ou mais, na direção de H₁. Ele **não** é a probabilidade de H₀ ser verdadeira.
>
> Nosso objetivo também é controlar erros: tipo I é sinalizar que a taxa excedeu 5% quando não excedeu; tipo II é deixar passar uma taxa que realmente excedeu. No CI, deixar passar problemas pode atrasar uma investigação, mas falsos alarmes também custam tempo; a gravidade depende desse contexto.

### Tela: seção 4 — G3

> Em G3, comparamos o erro tipo I ao nível nominal de 5%. Na condição de 30 execuções, o Z rejeitou indevidamente em 6,05% das simulações, ficando liberal, enquanto o binomial exato ficou em 1,69%, sendo conservador. Já com 200 execuções, ambos ficaram em 4,48%, próximos do nível escolhido.

### Tela: seção 5 — G4

> Em G4, vemos o poder: a chance de detectar que a taxa realmente supera a meta. O poder tende a aumentar conforme aumenta o tamanho do efeito. Com 30 execuções e taxa verdadeira de 10%, o Z atingiu 35,89% e o binomial exato 17,53%. Mas essa vantagem do Z veio acompanhada do excesso de falsos alarmes visto no G3.
>
> Com 200 execuções, as curvas coincidiram nos cenários estudados. A Fernanda vai fechar explicando o motivo dessa diferença e o que concluímos nos dados reais.

**Ponte visual:** G2 explica **o que cada teste calcula**; G3 mostra **falsos alarmes sob H₀**; G4 mostra **detecção quando H₁ é verdadeira**. Ao dizer 35,89% e 17,53%, apontar o cenário n = 30, p = 10% (efeito +5 pontos percentuais). Não apresentar maior poder do Z isoladamente como superioridade geral.

## Fala 3 — Fernanda (11–15)

### Tela: seção 5 — G4 e relação com G3

> A principal dificuldade da aproximação normal aparece quando temos poucas falhas esperadas. Com 30 execuções e uma meta de 5%, esperamos somente 1,5 falha sob H₀. Por isso, a distribuição discreta pode ficar distante da aproximação normal e os testes passam a tomar decisões diferentes. Com 200 execuções, esperamos dez falhas, e os dois testes tiveram o mesmo limiar de rejeição nas condições estudadas.
>
> Se reduzíssemos α de 5% para 1%, rejeitar H₀ se tornaria mais difícil: o erro tipo I e o poder só poderiam diminuir ou permanecer iguais, mantendo o mesmo cenário. **Isso é uma previsão metodológica, não um resultado calculado em G3/G4 para 1%.** O controle de α no G2 permite explorar a mudança de região crítica sem alterar os resultados oficiais.

### Tela: seção 6 — Dados reais

> Nos dados reais, observamos sete falhas em 169 execuções, ou 4,14%. O teste Z obteve p-valor de 0,6956 e o binomial exato, de 0,7452. Nenhum dos testes rejeitou H₀: não encontramos evidência suficiente para afirmar que a taxa supera 5%.
>
> A diferença observada para a meta foi de −0,86 ponto percentual. Esse tamanho do efeito indica a direção e a magnitude da diferença; não basta olhar só o p-valor, e não rejeitar H₀ também não prova que a taxa está necessariamente abaixo da meta.

### Tela: seção 7 — Conclusão

> A expectativa inicial era de maior dificuldade para o Z quando poucas falhas fossem esperadas. Foi o que observamos com n = 30; com n = 200, as decisões coincidiram nos cenários estudados.
>
> Por isso, recomendamos o binomial exato principalmente para falhas raras e amostras pequenas. O Z pode ser útil quando há contagens esperadas maiores. Nossa principal limitação é que assumimos execuções independentes e uma probabilidade de falha constante; na prática, execuções de CI podem compartilhar causas de falha. Além disso, os dados reais cobrem apenas um workflow e um período.

**Ponte visual:** o trecho sobre α = 1% é uma **hipótese de sensibilidade**, não uma nova curva em G3/G4; a barra lateral do G2 mostra que α pode ser explorado, mas não substitui uma simulação oficial. Na seção 6, apontar p-valores e a coluna de efeito; na seção 7, a expectativa, a recomendação e as limitações estão no texto do dashboard.

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
