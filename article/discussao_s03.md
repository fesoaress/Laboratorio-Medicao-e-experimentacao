## 4. Discussão

Comparamos os resultados com as hipóteses originais de `introducao.md`,
preservadas sem reescrita retrospectiva. As interpretações dizem respeito
às proxies e à amostra observada; não medem diretamente equipes ou
incidentes em produção.

### RQ01 — Frequência

A hipótese de concentração abaixo de uma release por semana foi
corroborada: 255/311 casos (82,0%) e mediana 0,326. A predominância
Medium/Low também ocorreu. A amplitude até 131,10/semana mostra que a
amostra inclui regimes muito distintos de publicação. Esses extremos
podem refletir automação e organização de versões, não necessariamente
maior frequência de implantações em produção. A hipótese individual H01,
de heterogeneidade, é compatível com o padrão observado.

### RQ02 — Lead time

A expectativa consolidada de mediana maior por commit foi contrariada:
118,17 h por commit contra 179,67 h por release. O LT por commit foi
menor em 171/261 pares. A própria justificativa original antecipava a
influência de commits antigos sobre o máximo por release; esse mecanismo
é compatível com a direção observada, embora a direção prevista na
hipótese fosse a oposta. A hipótese foi mantida como formulada.

O máximo dentro de uma release enfatiza a mudança mais antiga; a mediana
por commit pondera implicitamente intervalos com mais commits. Por isso
não há uma desigualdade universal entre as medianas agregadas: 85 casos
tiveram LT maior por commit. A assimetria e os extremos apoiam H02, mas
os 50 ausentes podem representar históricos mais complexos. Não é possível
atribuir a diferença exclusivamente a práticas melhores de entrega.

### RQ03 — Duas noções de falha

A hipótese CFR(a)>CFR(b) foi contrariada: medianas 5,29% e 22,73%, com
CFR(b) maior em 228/311 pares. As medidas capturam objetos diferentes.
CFR(a) observa conclusões de CI; CFR(b) classifica uma release original
pela ocorrência de qualquer corretiva posterior em até sete dias. Uma
mesma corretiva pode demonstrar a condição para vários originais, sem
duplicar cada original no numerador. Publicações frequentes ampliam as
oportunidades de satisfazer essa regra mesmo sem evidência de incidente.

Os 20.038 originais falhos de 26.444 avaliáveis são um resultado da regra
operacional, e não uma estimativa de que 75,78% das implantações causaram
incidentes. A diferença entre essa razão agregada, dominada por projetos
com muitas releases, e a mediana de 22,73% reforça a importância do grão
estatístico. A proposição H03 de menos falhas que sucessos é compatível
com a mediana, mas não descreve todo projeto nem a razão agregada.

A v5 tem 36 falsos positivos e 27 falsos negativos entre 300 casos, com
precisão 0,697 e recall 0,755. Falsas corretivas podem elevar CFR(b);
corretivas não detectadas podem reduzi-lo. Não sabemos o erro líquido na
população. As cinco versões foram ajustadas e avaliadas na mesma
amostra-ouro: F1=0,725 representa validação interna potencialmente otimista,
não validação externa nem prova de que a heurística identifica incidentes.

### RQ04 — Recuperação

A expectativa de medianas em horas foi corroborada pela mediana de
3,30 h, embora Q3=18,80 h e o máximo de 2.369,78 h mostrem heterogeneidade.
A previsão de censura merece qualificação: 114/10.254 episódios (1,11%)
foram censurados à direita. Isso não inclui falhas já em andamento no
início da janela, cujo início não é observado pela definição histórica.
Os 25 repositórios sem mediana não têm recuperação igual a zero. O
resultado caracteriza recuperação do workflow, que pode ser distinta da
restauração de um serviço em produção.

### RQ05 — Frequência e estabilidade

A hipótese de associação próxima de zero foi compatível com CFR(a):
rho=0,063, p_Holm de permutação=0,264 e IC95% [−0,051;0,180]. Isso não
prova equivalência ou ausência de qualquer relação. Para CFR(b), a
hipótese foi contrariada por rho=0,651 e IC95% [0,578;0,716].

Uma explicação plausível é o acoplamento entre a frequência e a regra
temporal de CFR(b): mais eventos em sete dias oferecem mais oportunidades
de observar uma corretiva. Essa é uma interpretação do desenho, não uma
causa demonstrada. Não concluímos que publicar mais provoca defeitos ou
que o estudo refuta resultados corporativos DORA, pois o construto e a
unidade de observação são diferentes.

### RQ06 — Fatores

A expectativa de melhor desempenho com popularidade não teve suporte
consistente: nenhum teste principal de estrelas permaneceu significativo
após Holm. Para contribuidores houve diferença global de LT
(p_Holm=0,0452; ε²=0,0502), mas o quartil superior teve mediana 339,18 h
contra 126,34 h no inferior, direção descritiva contrária à expectativa
de entregas mais rápidas. O resultado não demonstra um efeito causal do
número de contribuidores nem diferenças de todos os pares de quartis.

Idade apresentou os maiores efeitos observados para DF (ε²=0,1274) e LT
(ε²=0,1676), além de diferença menor em recuperação (ε²=0,0449). Projetos
mais antigos podem ter histórias, escopos e processos distintos; o desenho
não controla essas explicações concorrentes. A associação suplementar
idade×CFR(b) também não isola a influência da frequência de publicação.
A hipótese sobre linguagem não foi testada: escolhemos três fatores com
cobertura completa; não extrapolamos os tipos humanos dos 60 projetos.

### RQ07 — Sensibilidade

A expectativa de concordância geral moderada a substancial foi
corroborada nos pares calculáveis: Kappa 0,475/0,669/0,553. Ainda assim,
25,82%–36,48% dos repositórios pareados mudaram de categoria geral.
Uma classificação isolada deve ser acompanhada da definição operacional.

CFR foi o componente mais instável entre C1 e C2: 67,52% de mudanças e
κ=0,0157. A estabilidade geral maior que a desse componente é compatível
com a agregação de quatro escores, que pode amortecer alterações de um
componente. LT por commit C2×C3 teve concordância alta (κ=0,932), mas LT
C1×C2 e C1×C3 mudou em aproximadamente 47% dos pares. A coincidência de
CFR(a) em C1/C3 e de recuperação nas três combinações decorre de fontes
compartilhadas; não é uma validação independente.

Os n pareados gerais diferem (233, 213, 210), portanto suas diferenças de
Kappa não podem ser atribuídas somente às definições. A análise
suplementar na interseção comum de 210 casos manteve o padrão, com
Kappa 0,459/0,673/0,553. Isso reduz a preocupação com composição para
esse contraste, sem eliminar o viés das exclusões. O uso
de datas autorais de tags também expõe sequências sem ancestralidade
entre vizinhas e durações negativas; os casos permaneceram ausentes.
Foram 56 LT ausentes em C2 e 44 em C3. Esses problemas não justificam
trocar tags por releases estáveis nem eliminar o projeto das demais RQs.

### Contribuição original — Precisão das estimativas

O bootstrap acrescenta informação que um p-valor isolado não fornece:
por exemplo, o IC da mediana de CFR(b) foi [0,200;0,273], enquanto a
incerteza da correlação DF×CFR(a) inclui associações pequenas dos dois
sinais. Os resultados de DF×CFR(b) se mantiveram positivos nas faixas
estimadas. Essa precisão é condicional ao conjunto selecionado e às
proxies; não corrige a baixa validade de construto ou o possível erro da
heurística. Os intervalos não atribuem probabilidade de 95% ao parâmetro
fixo após a observação e não substituem os testes da RQ05/RQ06.

### RQ08 — Retrabalho e síntese para integração

A mediana de retrabalho de 42,11%, nos 274 projetos com classificação
integral, descreve o caráter corretivo das publicações. Ela não é a taxa
de originais potencialmente falhos. Os limites dos outros 37 casos
preservam a incerteza de classificação, sem converter previsões não
utilizáveis em negativas.

Os achados sustentam uma conclusão futura centrada em definições: a
frequência é predominantemente baixa, o LT depende da unidade de
agregação e a relação velocidade–estabilidade depende fortemente da
proxy de falha. A inovação explicita a precisão amostral dessas
estimativas, enquanto a sensibilidade evidencia a fragilidade de
comparar categorias sem informar sua operacionalização. A consolidação
final deve integrar estas seções ao modelo SBC e conferir o limite de dez
páginas, preservando as contribuições e referências existentes.
