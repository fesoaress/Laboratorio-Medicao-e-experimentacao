## 2. Metodologia — consolidação da S02

Estado em 20/10/2026, branch `Laboratorio-3`, HEAD inicial `a8428d2`.
Consolidam-se protocolo, definições no código e resultados verificáveis,
preservando as contribuições de Islayder em `introducao.md` e de Fernanda em
`metodologia_fernanda_s02.md`, com sua autoria/proveniência. Esta versão
incorpora a resolução humana, as cinco avaliações e o CFR(b) efetivamente
calculado; não apresenta hipóteses da introdução como resultados observados.

### Fonte, janela, população e seleção

Dados públicos da API REST/GraphQL do GitHub: metadados, releases, tags,
commits e workflow runs. Releases são proxies de entrega; Actions não prova
deploy em produção. A janela UTC `[2025-10-01, 2026-10-01)` tem fim exclusivo.
Essas datas foram definidas pelo grupo porque não constavam explicitamente
do material disponibilizado. A unidade principal é o repositório; default
branch e SHA observado são preservados para verificar ancestralidade.

Critérios: público, mais de 1.000 estrelas, Actions, default branch válida e
resolvida, pelo menos cinco releases estáveis publicadas na janela e ancestrais
do snapshot e 50 runs válidos `push` nessa branch, na mesma janela. Drafts,
prereleases e runs com conclusões ignoradas não contribuem para os limiares
aplicáveis. Erro de API não equivale a reprovação por contagem insuficiente.

| Etapa | Aprovações comprovadas | Reprovados nesta etapa | Não medidos |
|---|---:|---:|---:|
| Candidatos únicos | 1.782 | 0 | 0 |
| Públicos | 1.782 | 0 | 0 |
| Default branch identificada | 1.782 | 0 | 0 |
| Actions | 741 | 207 | 834 |
| Releases estáveis publicadas | 493 | 248 | 0 |
| Ancestralidade das releases | 379 | 72 | 42 |
| Runs válidos | 311 | 67 | 1 |
| Amostra final | 311 | 1.469 no total | 2 não resolvidos |

Fonte: `selection_funnel_s02.csv`. A ordem otimizada evita chamadas após uma
reprovação; não medido não significa negativo. As colunas intermediárias não
são categorias independentes de exclusão. Os 311 elegíveis têm 27.152 releases
estáveis na janela, 494.200 runs observados e 454.382 válidos. Busca por fatias
de estrelas/paginação e cache/checkpoints permitem coleta e retomada, mas a
ordem privilegia popularidade/disponibilidade. O smoke permanece separado.

### Métricas, variantes e censuras

**Deployment frequency (RQ01):** releases elegíveis por 365 dias, expresso
por semana (`n×7/365`) e mês (`n×30/365`). Ambas têm 311 observações válidas;
mês é uma unidade padronizada de 30 dias.

**Lead time (RQ02):** commits novos entre releases estáveis formam os
intervalos. A variante por release usa o commit mais antigo do intervalo;
a variante por commit usa os tempos individuais até a publicação. Por repo,
persistem mediana, Q1, Q3 e IQR com interpolação linear (tipo 7). Ambas têm
261 valores válidos e 50 ausentes (29 erros de comparação, 21 de métrica).
Predecessoras externas à janela são preservadas; ausência de predecessora,
intervalo sem novos commits e compare 404 ficam explícitos. Durações negativas
não são truncadas para zero. Falha posterior de enriquecimento não exclui
repositório elegível nem inventa observações.

**CFR(a), proxy de CI (RQ03):** `failure/(success+failure)` em runs válidos,
com timeout/startup failure normalizados pelo pipeline. Conclusões ignoradas
ficam fora da razão; denominador zero é ausente. Há 311 valores válidos.

**CFR(b), proxy de entrega (RQ03):** heurística validada v5 aplicada às 27.152
releases da população. O grupo confirmou: cada original falha se existe
qualquer release estável estritamente posterior, corretiva, até R+7 dias
inclusive; intermediárias não corretivas não impedem a evidência. Essa decisão
sobre intermediárias operacionaliza o enunciado. Cada original conta uma vez.
Originais a partir de `2026-09-24T00:00:00Z` são censurados incondicionalmente,
mesmo com positiva observada; ainda podem ser evidência para anteriores.
Sem positiva conhecida, classificação posterior indisponível torna o original
não calculável. Ausência de predecessora não exclui o original; não se inventa
patch nessa ausência. Só eventos dentro da janela entram no cálculo.

`CFR(b) = failed/(failed+not_failed)` por repo. São **311 valores/fontes válidos,
zero ausentes**. A partição de releases é 20.038 falhas, 6.406 não falhas,
677 censuradas e 31 não calculáveis; denominador global 26.444. Não se usa essa
razão agregada como se fosse o valor de cada repo. Denominador zero seria
ausente, não zero artificial. A política `any_corrective_7d_v1`, as fontes e
a avaliação v5 constam do manifesto e de cada `cfr_delivery_source`.

**Recovery time (RQ04):** por workflow, o episódio inicia na primeira falha
após um sucesso observado e termina na conclusão do retorno a sucesso.
Falhas iniciais sem sucesso anterior não identificam o início do episódio
(limitação de censura à esquerda). Ausência de recuperação até o fim gera
censura à direita: preserva-se a proporção, excluindo censurados da mediana.
Há 286 medianas válidas e 25 ausentes (23 sem episódios e dois repos somente
com episódios censurados). A proporção é calculável em 288 repos, ausente
nos 23 sem episódios. Contagens e episódios individuais estão persistidos.

Variantes semana/mês, release/commit, quartis/IQR e diagnósticos de censura
permitem análise posterior; CFR(b) completa as entradas das combinações de
definições de RQ07. Nenhuma classificação DORA ou análise da S03 foi inventada.

### Amostra-ouro, avaliações e Kappa

Seed **42**: sorteio de **60 repositórios** dentre os **311 elegíveis** e
**cinco releases reais por repositório**, total **300 itens**. As identidades
são ordenadas previamente; a seed de releases deriva de SHA-256 de
`42:identidade_normalizada`. Manifesto preserva IDs, algoritmo e hashes.

Islayder, Fernanda e Vinicius avaliaram independentemente tipo de projeto,
representatividade e caráter corretivo. As duas primeiras dimensões são de
repositório (repetidas nas cinco linhas); a terceira é por release. Os três
CSV individuais passaram em 60/60, 300/300, zero erros, mesma amostra e contexto.
SHA-256 anteriores/posteriores comprovam preservação dos arquivos humanos.

Fleiss Kappa foi calculado por statsmodels sobre votos originais, antes do
consenso, separadamente para 60/60/300 itens:

| Dimensão | Kappa | Interpretação do protocolo |
|---|---:|---|
| Tipo | 0,8628963153384747 | Quase perfeita |
| Representatividade de entrega | 0,15401301518438168 | Leve |
| Release corretiva | 0,7352941176470585 | Substancial |

Protocolo: unanimidade ou maioria simples (2×1); três categorias diferentes
exigem revisão humana. São 350 unanimidades, 69 maiorias e um empate triplo,
totalizando 70 divergências. Em `armbian/build`, representatividade, os votos
foram `no`/`uncertain`/`yes` (Islayder/Fernanda/Vinicius). Islayder resolveu
como **`no`**, justificando que as releases são resumos "Armbian Weekly digest"
do framework de build, enquanto imagens destinadas aos usuários são distribuídas
por outros canais oficiais. A justificativa integral está em
`manual_resolutions.csv`. Foi a única resolução manual, sem mudar os três
CSV individuais. O consenso completo valida 60×5 sem erros. A execução inicial
e seu template vazio estão preservados em `pre_manual/`; Kappa antes/depois
é byte a byte idêntico. Não se usou classificador ou IA no desempate.

### Validação empírica da heurística

Baseline existente v1: incremento apenas de patch SemVer ou sinal corretivo
em assunto de commit. Alternativa v2: predominância de correções frente a
features em notas/commits, com regras de manutenção e fallback de patch.
Predecessoras vêm do histórico completo, não da ordem do sorteio.
Os 300 itens do consenso, classe positiva `corrective_release=yes`, foram
comparados por identidade usando scikit-learn. Precision=TP/(TP+FP),
recall=TP/(TP+FN), F1=2TP/(2TP+FP+FN), com flags para denominadores indefinidos.

| Versão | Precision | Recall | F1 | Resultado |
|---|---:|---:|---:|---|
| v1 | 0,380952 | 0,872727 | 0,530387 | Refinar |
| v2 | 0,479638 | 0,963636 | 0,640483 | Refinar |
| v3 | 0,905660 | 0,436364 | 0,588957 | Refinar |
| v4 | 0,863636 | 0,518182 | 0,647727 | Refinar |
| **v5** | **0,697479** | **0,754545** | **0,724891** | **Aceita** |

v3 exigiu maioria estrita entre todas as mudanças; v4 removeu manutenção e
entradas administrativas desse denominador. Ambas perderam recall. v5 refinou
o balanço lexical de v2 para reconhecer adições/introduções/suporte/melhorias
como sinais funcionais concorrentes e removeu o fallback de patch isolado.
Não há condições por repo, tag específica, item ou rótulo humano no classificador.
**v5** é a primeira que atingiu F1≥0,70; TP=83, FP=36, FN=27, TN=154.
Não houve refinamento após aceitação. Todas as execuções preservam código,
fontes, hashes, previsões e métricas em pastas distintas. A inspeção dos erros
e as cinco reavaliações na mesma amostra geram otimismo de seleção: são
validação interna, sem teste externo independente. Fixtures de testes não
constituem resultados do estudo. A versão aceita fundamenta CFR(b).

### Auditoria, reprodutibilidade e limitações

`python -m src.s02_quality` audita o dataset de 311 linhas/48 colunas contra
as fontes, domínios/tipos, unicidade, fórmulas, quartis/IQR e denominadores.
O resultado atual tem zero erros nas verificações implementadas e status
`valid`, com hashes, perfil de ausentes, motivos e partição de CFR(b).
Não reescreve dataset/rótulos e não confunde ausente com zero.

Retenção de runs e objetos apagados limitam a recuperação histórica. Tags
movidas exigem objetos/snapshots preservados. Popularidade, ordem de busca,
disponibilidade de contexto e erros de enriquecimento limitam generalização.
Releases/termos corretivos não provam deploy, incidente ou causalidade entre
versões. O Kappa leve de representatividade também limita interpretar toda
release como entrega real, mesmo após consenso por maioria.

Fontes: `docs/s02_collection.md`, `s02_validation.md`, `s02_consolidation.md`,
`data_dictionary.md`, manifests da S02, `data/validation/fleiss_kappa.csv`,
`analysis_status.json`, `dataset_metrics_audit.json` e
`data/gold_sample/disagreements.csv`. As pendências estão detalhadas em
`reports/lab03_s02_validation.md`.
