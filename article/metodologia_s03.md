## Extensão metodológica da Sprint 03

Analisamos os 311 repositórios selecionados na S02, sem refazer a seleção,
na janela UTC [2025-10-01, 2026-10-01). O repositório é a unidade estatística:
medianas da população de repositórios não são médias nem razões agregadas de
todos os eventos. A auditoria independente verifica rótulos, consenso,
avaliações v1–v5, fórmulas, fontes e hashes, preservando a base homologada.
As decisões humanas anteriores continuam em seus arquivos originais.

### Descrição e classificação

Para cada métrica reportamos n, ausentes, mediana, Q1, Q3, IQR, mínimo e
máximo. Os quartis usam interpolação linear tipo 7. Frequência é a contagem
de releases estáveis dividida por 365/7 semanas; o mês operacional tem 30
dias. Lead time por release usa o commit mais antigo de cada intervalo e,
depois, a mediana das releases. A variante por commit usa a mediana de todas
as observações commit–entrega do repositório. Não há ponderação adicional
por popularidade ou volume entre repositórios.

CFR(a) usa falhas/(falhas+sucessos) dos runs válidos. CFR(b) segue a política
homologada `any_corrective_7d_v1`: qualquer corretiva posterior em até sete
dias pode demonstrar a falha de uma release original. A censura a partir de
2026-09-24 é incondicional. Recuperação usa episódios resolvidos; censuras
continuam contabilizadas separadamente. Campos ausentes não viram zero;
cada análise usa somente as variáveis de que necessita e informa seu n.

Categorias DORA, seguindo o protocolo do laboratório:

| Métrica | Elite | High | Medium | Low |
|---|---|---|---|---|
| DF | ≥7/semana | ≥1/semana e <7 | ≥1/30 dias e <1/semana | <1/30 dias |
| LT (h) | <24 | [24,168) | [168,720) | ≥720 |
| CFR (fração) | ≤0,15 | (0,15;0,30] | (0,30;0,45] | >0,45 |
| Recuperação (h) | <1 | [1,24) | [24,168) | ≥168 |

Low=1, Medium=2, High=3, Elite=4. A categoria geral é o piso da mediana dos
quatro escores e exige as quatro métricas. C1 usa DF estável, LT por release,
CFR(a) e recuperação. As duas variantes de LT e de CFR também recebem
classificações individuais, sem trocar a referência retrospectivamente.

### RQ05 e RQ06

Aplicamos `scipy.stats.spearmanr` aos pares DF×CFR(a) e DF×CFR(b), com
exclusão apenas por par. Além do p assintótico obrigatório, usamos um teste
bilateral de permutação: 9.999 permutações dos postos de CFR, seed 42,
p=(extremos+1)/10.000. Isso evita depender somente da aproximação assintótica
com n=311. Holm corrige conjuntamente os dois p de permutação. Adotamos
α=0,05. Intensidades são descritas pelos valores de rho, sem transformar
ausência de significância em equivalência nem associação em causalidade.

Os três fatores da RQ06 são estrelas, contribuidores e idade, disponíveis
nos 311 casos. Tipo do projeto tem somente 60 rótulos; não foi extrapolado.
Quartis são calculados na população completa antes da exclusão por métrica;
intervalos fecham à direita e empates nunca são divididos artificialmente.
Grupos vazios e grupos com n<5 impedem Kruskal–Wallis. Dois grupos válidos
usam Mann–Whitney bilateral assintótico; três ou mais usam Kruskal–Wallis.

A família principal contém 12 testes (3 fatores × DF, LT por release,
CFR(a), recuperação), corrigidos conjuntamente por Holm. Os três testes
suplementares de CFR(b) formam outra família explícita. Reportamos estatística,
p bruto e ajustado, n, tamanhos dos grupos, medianas e IQR. Seguindo a fórmula
do professor, ε²=H/(n−1); para dois grupos, delta de Cliff=2U/(n1·n2)−1.
Não inferimos quais pares de grupos diferem a partir do teste global.
Não realizamos seleção posterior de testes para maximizar significância.

### RQ07: sensibilidade das definições originais

O grupo autorizou a coleta pontual das comparações faltantes, mantendo:

| Combinação | Entregas para DF | LT | CFR | Recuperação |
|---|---|---|---|---|
| C1 | Releases estáveis | Por release | (a) runs | CI, comum |
| C2 | Releases estáveis + pré-releases | Por commit | (b), eventos de C2 | CI, comum |
| C3 | Tags ancestrais da default branch | Por commit | (a) runs | CI, comum |

Cada variante é ordenada por seu tempo factual e identificador. C2 usa
`published_at`; C3 usa `authoredDate` do commit apontado, inclusive quando
diverge da publicação de uma release. Commits são os do intervalo entre
os SHAs corretos da variante. A ancestralidade da default branch usa o
snapshot S02. Reutilizamos um export estável somente quando ambos os SHAs
coincidem exatamente e a comparação está completa; SHAs idênticos comprovam
intervalo vazio. Não copiamos uma mediana de outra definição.

O coletor próprio usa cache, retomada, backoff, paginação e conferência de
totais. GraphQL só é aceito após verificar OIDs; REST por SHA é o fallback.
O Git completo do WPT evita chamadas redundantes. As predecessoras anteriores
à janela são contexto, não eventos adicionados ao denominador: pré-releases
de fronteira são recuperadas do histórico bruto S02; tags de fronteira usam
o catálogo em cache e ancestralidade comprovada. Contexto que permanece
indisponível é identificado, sem afirmar que se trata da primeira entrega
real do projeto. Comparações inválidas e LT negativo deixam o LT do
repositório ausente; 404 e ausência de predecessora observada são exclusões
de intervalo rastreadas, conforme a política histórica. Não descartamos o
repositório das demais métricas.

A heurística aceita v5 é aplicada ao histórico combinado de C2, com notas
prioritárias e commits próprios do intervalo. A extensão a pré-releases
não possui validação humana externa adicional; isso limita a interpretação.
Mantemos a mesma regra de sete dias e censura, agora sobre os eventos de C2,
sem modificar o CFR(b) estável homologado. Cada comparação C1×C2, C1×C3,
C2×C3 usa apenas os repositórios com ambas as categorias válidas. Calculamos
mudanças, percentual e Kappa de Cohen ponderado linearmente, na ordem
Low<Medium<High<Elite. Casos constantes têm Kappa indefinido, não igual a 1.
Reportamos métricas individuais e categoria geral; uma alta concordância
não valida a proxy como medida de incidentes em produção.

### Inovação: incerteza por bootstrap

Não foi encontrada inovação prévia formalizada do Lab03 nas fontes
consultadas. Implementamos IC percentil 95% com 2.000 reamostragens de
repositórios, seed 42, para as medianas de DF, CFR(a), CFR(b) e os dois rho
da RQ05. Para correlações o par inteiro é reamostrado, preservando o vínculo.
Réplicas constantes são excluídas e contadas; uma estimativa original
indefinida permanece indefinida. O bootstrap descreve a precisão condicional
à amostra e às proxies: não corrige viés de seleção, dependência entre
projetos ou erro da heurística e não substitui os testes obrigatórios.

### RQ08: retrabalho

Calculamos corretivas/total de releases estáveis. Quando existem previsões
não utilizáveis, a taxa pontual permanece ausente; reportamos limites
identificáveis [corretivas conhecidas/total,
(corretivas conhecidas+desconhecidas)/total]. Esses limites não são ICs.
Rework conta corretivas; CFR(b) conta originais seguidas por corretiva.

### Implementação e referências de cálculo

Os módulos `src/s03*.py` exportam tabelas e figuras PNG/SVG/PDF. Os manifests
registram SHA-256 de entradas/saídas, versões de bibliotecas e seeds.
Reexecutar as análises offline não exige credencial nem nova seleção.
As instruções e decisões detalhadas estão em `docs/s03_analysis.md`.

Referências técnicas: [Spearman/SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.spearmanr.html),
[Kruskal–Wallis/SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.kruskal.html),
[Holm/statsmodels](https://www.statsmodels.org/stable/generated/statsmodels.stats.multitest.multipletests.html),
[Kappa/scikit-learn](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.cohen_kappa_score.html).
