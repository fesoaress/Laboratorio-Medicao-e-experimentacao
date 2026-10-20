## Ameaças à validade — material para integração final

**Construto.** Releases, pré-releases e tags não equivalem necessariamente
a implantações em produção. O Kappa de representatividade de entregas
foi apenas 0,154013, evidência de dificuldade operacional entre humanos;
o consenso posterior não apaga essa baixa concordância. Runs de CI e
recuperação de workflows também não medem diretamente incidentes e
restauração de serviços. CFR(b) associa temporalmente corretivas a
originais e pode classificar vários originais a partir de uma corretiva.
Seu acoplamento com a frequência e o horizonte de sete dias limita a
interpretação de rho=0,651. Datas autorais de commits podem anteceder muito
o merge ou ter ordenação incompatível com a ancestralidade; a data de
publicação da release tem outro significado. A classificação DORA usa os
limites especificados no laboratório, não uma nova validação desses
limites para projetos open-source.

**Interna.** A v5 alcançou F1=0,724891 após cinco avaliações no mesmo
consenso, com 36 FP e 27 FN; há risco de otimismo e erro de classificação
na população. Sua extensão a pré-releases não dispõe de nova amostra
humana independente. Não atribuímos causalidade a correlações ou a
diferenças por quartis: idade, complexidade, organização de versões,
popularidade e contribuidores podem se confundir. Tags removidas/movidas
e referências indisponíveis limitam a reconstrução; SHAs fixos, cache e
auditoria preservam evidências sem eliminar essas ameaças. Ausência ou
404 da predecessora de fronteira exclui o primeiro intervalo observado;
não comprova inexistência histórica de entregas anteriores.

**Externa.** A seleção favorece repositórios públicos com mais de mil
estrelas, Actions, pelo menos cinco releases estáveis e 50 runs válidos
na default branch. Há 311 elegíveis após 1.782 candidatos processados;
não se trata de amostra aleatória de todo o GitHub nem de equipes
corporativas. A ordem da busca e a disponibilidade técnica influenciam
a composição. A janela de 12 meses foi definida pelo grupo. Não
generalizamos o tipo de projeto rotulado em 60 casos aos demais 251.
Dependências e mantenedores compartilhados entre projetos podem reduzir
a independência efetiva das observações.

**Conclusão.** Há 50 LT ausentes na referência e 25 recuperações ausentes;
a categoria geral C1 usa somente 239 repositórios. Os n pareados gerais
RQ07 são 233/213/210, afetando a comparabilidade entre coeficientes. Em
C2/C3, comparações não ancestrais, 404, erro 422 e durações negativas
permanecem explícitos. A exclusão por análise evita zeros artificiais,
mas não elimina viés se a falta de dados estiver associada à complexidade.
A mediana de recuperação exclui episódios censurados e pode subestimar
o tempo de falhas longas; episódios já iniciados antes da janela têm
censura à esquerda. Holm controla as famílias declaradas, mas não torna
um efeito pequeno relevante nem identifica pares específicos após um
Kruskal–Wallis global. Permutação e bootstrap consideram repositórios
como unidades independentes, hipótese que pode ser aproximada. ICs
percentis com 2.000 réplicas quantificam variação amostral, não os vieses
de seleção, erros de proxy ou incerteza de todas as decisões metodológicas.
