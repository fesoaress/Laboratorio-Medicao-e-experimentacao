# Lab04 — Apresentação final e defesa

Use o dashboard da branch `Laboratorio-4` com os parâmetros oficiais
`p₀ = 0,05` e `α = 0,05`. Se precisar abrir localmente, siga o
[README do Lab04](../README.md). O roteiro prevê **6min40s de fala e 20s de
margem**. O grupo deve cronometrar o ensaio.

## Roteiro de até sete minutos

| Tempo | Integrante | O que mostrar e dizer |
|---|---|---|
| 0:00–2:05 | Fernanda | Seções 1 e 2, G1. Apresente a pergunta sobre a meta de 5%, as hipóteses e a origem dos dados. Compare as duas distribuições binárias e identifique a amostra simulada. Antecipe a conclusão observacional da seção 6 com sete falhas em 169 execuções. |
| 2:05–4:15 | Islayder | Seção 3, G2. Mostre as duas caudas e regiões críticas da mesma amostra. Explique como a simulação usa o mesmo K nos dois testes, com 10.000 repetições por cenário, seis efeitos e semente 42. Defina erro tipo I no efeito zero e poder nos efeitos positivos. |
| 4:15–6:40 | Vinicius | Seções 4 e 5, G3 e G4. Compare n = 30 e n = 200 e explique a diferença dos limiares. Passe pelas seções 6 e 7 para mostrar os p-valores reais, a diferença de −0,86 p.p., a recomendação e as limitações. |
| 6:40–7:00 | Grupo | Margem para transições e fechamento. |

## As 15 perguntas de defesa

A numeração e a divisão seguem as Issues [#84](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/84),
[#85](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/85)
e [#86](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/86).
Todos devem conseguir responder a qualquer pergunta.

### 1. Qual é o cenário e quais são H₀ e H₁? · Fernanda

Investigamos se a probabilidade de falha do workflow **Test** do FastAPI
ultrapassa 5%. H₀ é p ≤ 0,05 e H₁ é p > 0,05. O nível nominal é α = 0,05.

### 2. O teste é unilateral ou bilateral? Por quê? · Islayder

É unilateral à direita porque a pergunta é se p **ultrapassa** a meta.
Contagens altas de falhas dão evidência na direção de H₁.

### 3. Como coletamos os dados e qual é a distribuição? · Fernanda

Usamos a API pública do GitHub Actions para execuções de `push` na branch
`master`, de 1º de julho a 30 de setembro de 2026 (UTC). Incluímos 162
sucessos e sete falhas e excluímos oito cancelamentos. Cada resultado é
Bernoulli (0/1). Com independência e p constante, o total K é binomial.

### 4. Como os dados reais definiram os parâmetros da simulação? · Fernanda

A amostra real mostrou o desfecho binário e deu a escala de n = 169.
Usamos n = 200 como referência e n = 30 para testar a aproximação em
amostra pequena. A meta de 5% vem da pergunta do estudo e define o
efeito zero. Os outros cinco cenários usam probabilidades de 7,5% a 20%.

### 5. O que os dois testes comparam? · Islayder

Os dois usam a mesma contagem k e o mesmo n. O Z padroniza p̂ − p₀ pelo
erro-padrão sob p₀ e calcula a cauda normal. O binomial exato calcula
P(K ≥ k) sob K ∼ Binomial(n, p₀).

### 6. Quais são as distribuições sob H₀ e as regiões de rejeição em G2? · Vinicius

Na fronteira de H₀, K segue Binomial(n, p₀) e a referência aproximada do
Z é N(0,1). A região crítica fica à direita. Em n = 30, p₀ = 5% e α = 5%,
o Z rejeita com K ≥ 4 e o exato, com K ≥ 5.

### 7. Como interpretar o p-valor em G2? · Islayder

É a probabilidade, calculada sob p = p₀, de obter uma estatística pelo
menos tão extrema na direção de H₁. O Z usa uma aproximação nessa
probabilidade. O p-valor é condicionado a H₀ e a magnitude é medida
separadamente pelo tamanho do efeito.

### 8. Quais são os erros tipo I e II e qual é mais grave? · Islayder

Tipo I é sinalizar taxa acima da meta quando p ≤ 5%. Tipo II é deixar
passar uma taxa realmente acima da meta. O tipo II pode ser mais grave
quando atrasar uma investigação tem custo alto. A prioridade depende
também do custo dos falsos alarmes.

### 9. Quem foi liberal ou conservador em G3? · Vinicius

Em n = 30, o Z foi liberal (6,05%) e o exato, conservador (1,69%). Em
n = 200, ambos ficaram abaixo do nível nominal, com 4,48%. A taxa
analítica na fronteira foi 4,436% para ambos nesse n.

### 10. Qual teste teve mais poder e como ele muda com o efeito em G4? · Vinicius

O poder aumentou com o efeito. Em n = 30, o Z rejeitou mais em todos os
efeitos positivos, junto de uma taxa de falso alarme acima de 5%. Para
p = 10%, as taxas foram 35,89% e 17,53%. Em n = 200, os testes tiveram o
mesmo limiar e as curvas coincidiram nos cenários estudados.

### 11. Qual pressuposto foi problemático e qual foi o efeito? · Fernanda

Em n = 30, esperamos apenas 1,5 falha sob p₀. A normal aproxima mal a
cauda dessa contagem discreta e o Z rejeita já com quatro falhas. O exato
requer cinco. Em n = 200, esperamos dez falhas e ambos rejeitam a partir
de 16, para os parâmetros do estudo.

### 12. O que mudaria em G3/G4 se α caísse para 1%? · Islayder

A região crítica diminuiria ou ficaria igual devido aos saltos discretos.
Para o mesmo n e efeito, erro tipo I e poder só podem cair ou permanecer
iguais. Os valores para α = 1% exigem recálculo.

### 13. A simulação confirmou a expectativa inicial? · Vinicius

Sim. A S01 antecipava maior dificuldade para o Z com poucas falhas
esperadas. A simulação mostrou divergência em n = 30 e, nos parâmetros
estudados, coincidência das decisões em n = 200.

### 14. Qual foi a conclusão real e por que importa o tamanho do efeito? · Fernanda

Sete falhas em 169 execuções dão 4,14%. O Z foi −0,512 (p = 0,6956) e o
binomial exato teve K = 7 (p = 0,7452). A evidência foi insuficiente para
concluir que a taxa excede 5%. A diferença observada de −0,86 p.p. mostra
a magnitude e a direção do desvio em relação à meta.

### 15. Qual teste recomendar, quando mudar e qual é a principal limitação? · Vinicius

Prefira o binomial exato para falhas raras, sobretudo com poucas falhas
esperadas. O Z pode ser útil quando as contagens esperadas são maiores.
A inferência pressupõe independência e p constante, e a coleta cobre um
workflow em um período. Execuções próximas podem compartilhar causas de
falha.

## Evidências para a revisão do grupo

- [Cenário e dados reais](cenario_s01.md) e [CSV versionado](../data/ci_runs.csv).
- [Desenho de Q1/Q2](s02_q1_q2.md), [resultados e limiares de Q3](s02_q3.md)
  e [auditoria final](final_verification.md).
