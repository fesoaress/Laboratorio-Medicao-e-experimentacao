# Metodologia S02 — contribuição de Fernanda (#55, #58)

Este fragmento descreve a contribuição local em 12/10/2026. O arquivo individual
foi preenchido e validado. Concordância, consenso e validação empírica da
heurística ainda estão pendentes; atualizar essas etapas após sua execução.

A amostra-ouro já preparada pelo grupo contém 60 repositórios, sorteados com
semente fixa 42 dentre 311 elegíveis, e cinco releases estáveis por repositório.
A janela de observação é `[2025-10-01, 2026-10-01)`, em UTC. Cada avaliador
classifica independentemente tipo de projeto, representatividade das releases
como entregas e caráter predominantemente corretivo das 300 releases, sem
consultar votos de colegas ou resultados do classificador.

Foi implementado um formulário local de apoio à revisão de Fernanda. Ele
apresenta somente contexto factual coletado e suas próprias respostas, permite
salvamento parcial e conserva os identificadores, notas originais e contexto
de commits. Os dois rótulos de projeto são replicados nas cinco linhas para
evitar inconsistência. Uma validação verifica completude, categorias, integridade
da amostra e consistência. A ferramenta não decide os rótulos humanos.

A implementação de identificação automática contém duas políticas iniciais
versionadas, descritas integralmente em `docs/s02_fernanda.md`. A baseline v1
usa mudanças de patch SemVer ou sinais corretivos nos assuntos dos commits.
A alternativa v2 busca predominância de correções frente a features nas notas
ou commits, com tratamento de manutenção explicitamente tipada. Nenhuma melhoria
de v2 foi demonstrada empiricamente nesta etapa. As versões de referência são
obtidas do histórico completo de releases estáveis, e não da ordem do sorteio.

O consenso será disponibilizado após a concordância e a discussão das
divergências, conduzidas pelo responsável pela #57. A avaliação automática
somente pode ocorrer depois de a rotulagem de Fernanda e o consenso estarem
completos. Serão comparadas as 300 decisões corretivas por `item_id`, com `yes`
como classe positiva. Precisão, recall e F1 são calculados por
`sklearn.metrics.precision_recall_fscore_support`, com matriz de confusão e
denominadores indefinidos explicitamente registrados. F1 inferior a 0,70 exige
refinamento e nova avaliação; cada execução conserva fontes, hashes, código
avaliado, versão e resultados em uma pasta distinta.

Erros na disponibilidade dos commits são contados e não removem silenciosamente
releases da validação. A regra binária usa os sinais disponíveis, o que pode
produzir falsos negativos quando o contexto é incompleto. Patch e termos
corretivos são proxies: não demonstram que o defeito era recente nem que a release
anterior o causou. Reajustar regras com o mesmo consenso pode gerar otimismo;
os resultados devem ser descritos como validação interna da heurística.

O arquivo individual registra as justificativas por release e os casos mistos.
A validação confirmou 60 projetos, 300 releases e preservação do contexto original,
sem erros. A decisão considerou o objetivo principal da versão; manutenção,
atualização de metadados, desempenho e novas funcionalidades foram distinguidos
de reparos. Changelogs históricos copiados nas notas não foram atribuídos
integralmente à release atual. Evidência ausente ou parcial e fontes adicionais
foram registradas nas observações. Os rótulos individuais ainda podem divergir
dos demais e não constituem o consenso da amostra.

Pendências para substituir este fragmento pelo relato final: referência aos resultados da #57,
versões efetivamente avaliadas, justificativas dos ajustes, métricas empíricas
e versão incorporada ao cálculo de CFR(b).
