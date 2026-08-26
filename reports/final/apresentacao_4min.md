# Apresentação final do Lab01 — roteiro de 4 minutos

## Objetivo e orçamento de tempo

A apresentação deve contar a sequência: objetivo → 1.000 repositórios → seis questões → evidências → interpretação → conclusão. Não abrir código durante os quatro minutos.

| Pessoa | Conteúdo | Meta de fala | Faixa de palavras |
|---|---|---:|---:|
| Pessoa 1 — Islayder | objetivo/metodologia, RQ01, RQ02 e robustez | 1min20s | 175–195 |
| Pessoa 2 — Fernanda | RQ03 e RQ04 | 1min05s–1min10s | 145–165 após preencher |
| Pessoa 3 — Vinicius | RQ05, RQ06 e conclusão | 1min05s–1min10s | 145–165 após preencher |
| **Total planejado** | — | **3min40s–3min50s** | **aprox. 480–500** |

O roteiro atual tem aproximadamente 483 palavras de fala. Com ritmos planejados de 140 ppm para a Pessoa 1, 130 ppm para a Pessoa 2 e 135 ppm para a Pessoa 3, mais 10–15 segundos de pausas e transições, a estimativa é de 3min44s–3min49s. As falas de RQ03–RQ06 abaixo são templates; o tempo deve ser confirmado novamente depois que os campos forem preenchidos e ensaiados.

## Pessoa 1 — fala completa

> Boa noite. Nosso objetivo foi caracterizar os mil repositórios mais estrelados do GitHub por seis questões de pesquisa. Os dados foram coletados automaticamente pela API GraphQL e analisados com estatísticas descritivas e gráficos.
>
> Na RQ01, perguntamos se sistemas populares são maduros. A idade mediana foi de 2.821 dias, aproximadamente 7,7 anos. A amostra, porém, vai de apenas 2 até 6.701 dias. Isso sugere predominância de projetos maduros, mas também mostra que popularidade não é exclusiva de projetos antigos. Por isso, consideramos a hipótese parcialmente confirmada.
>
> Na RQ02, usamos a quantidade de pull requests incorporadas, ou PRs merged, como indicador de atividade colaborativa. A mediana foi 765,5, enquanto a média chegou a 4.210,6. Essa diferença, junto da forte assimetria, mostra que uma parcela minoritária de projetos concentra volumes extremos. A métrica descreve PRs incorporadas, mas não prova contribuição externa.
>
> Como análise complementar, aplicamos o critério IQR. A RQ01 permaneceu estável. Na RQ02, retirar extremos apenas na análise de sensibilidade reduziu a média em 67,44%, contra 23,97% na mediana. Isso reforça que a mediana representa melhor o caso típico. Agora a Fernanda apresenta as RQ03 e RQ04.

### Marcação de ritmo da Pessoa 1

- Objetivo e método: cerca de 15–16s.
- RQ01: cerca de 24–26s.
- RQ02: cerca de 27–30s.
- Robustez e transição: cerca de 12–14s.
- Não explicar paginação, checkpoint ou a fórmula completa do IQR.

## Pessoa 2 — template para preencher

### RQ03 — cerca de 28–30s

> Na RQ03 investigamos se sistemas populares lançam releases com frequência. A mediana foi de 39,5 releases por repositório, com forte assimetria à direita. O gráfico mostra que 28% dos repositórios têm zero releases — não por falta de atividade, mas porque projetos de documentação e curadoria não usam esse mecanismo do GitHub. Assim, classificamos a hipótese como parcialmente confirmada: projetos de software ativo lançam releases com frequência moderada, mas uma parcela relevante do top 1.000 simplesmente não adota esse fluxo. Vale destacar que a API retorna no máximo 1.000 releases; 21 repositórios atingiram esse teto e o valor real pode ser superior.

### RQ04 — cerca de 28–30s

> Na RQ04 analisamos se sistemas populares são atualizados com frequência. A mediana foi de apenas 3 dias desde o último push, e 60% dos repositórios tiveram push nos últimos 7 dias. A visualização confirma forte concentração em valores baixos, com uma cauda de projetos sem atualização há mais de um ano — como editores descontinuados que mantêm as estrelas do passado. Portanto, a hipótese foi confirmada para a maioria: repositórios populares são ativamente mantidos. A medida representa o estado na data da coleta, agosto de 2026, e não pode ser extrapolada para outros momentos.

### Transição

> Em seguida, o Vinicius apresenta as RQ05 e RQ06 e integra a conclusão do estudo.

## Pessoa 3 — templates para preencher

### RQ05 — cerca de 25–27s

> Na RQ05 verificamos se os sistemas populares usam as linguagens mais populares. A distribuição foi liderada por **[LINGUAGENS E PERCENTUAIS PRINCIPAIS]**. Comparando com o **TIOBE Index de agosto de 2026**, observamos **[CONVERGÊNCIAS E DIVERGÊNCIAS]**. Assim, a hipótese foi **[CONFIRMADA/PARCIALMENTE CONFIRMADA/REFUTADA]**, porque **[INTERPRETAÇÃO]**. Os dois rankings usam conceitos diferentes de popularidade, o que limita uma comparação direta.

### RQ06 — cerca de 25–27s

> Na RQ06 avaliamos o percentual de issues fechadas. Encontramos **[MEDIANA OU VALOR PRINCIPAL]**, com **[QUARTIS, AMPLITUDE OU PERCENTUAL RELEVANTE]**. O gráfico mostra **[PADRÃO E POSSÍVEIS EXCEÇÕES]**. A hipótese foi **[CONFIRMADA/PARCIALMENTE CONFIRMADA/REFUTADA]**, pois **[INTERPRETAÇÃO]**. Repositórios sem issues devem permanecer identificados como razão indefinida, e não como zero.

### Conclusão — cerca de 15–18s

> Em conjunto, os resultados indicam **[SÍNTESE REAL DE RQ01–RQ06]**. Os projetos são heterogêneos, e métricas como estrelas, PRs, releases, linguagem principal e issues funcionam como proxies com limitações. A análise complementar mostrou **[CONTRIBUIÇÃO DA ROBUSTEZ]**. Assim, concluímos **[CONCLUSÃO GERAL APOIADA PELOS SEIS RESULTADOS]**.

## O que mostrar na tela

1. **Pessoa 1 — RQ01:** deixar visível a página 6 do relatório, com `rq01_age_histogram.png`.
2. **Pessoa 1 — RQ02:** trocar uma única vez para a página 7, com `rq02_merged_prs_log_histogram.png`.
3. **Robustez:** mencionar sem trocar de página. O gráfico `rq01_rq02_robustness_percent_change.png`, na página 8, fica como apoio para pergunta do professor.
4. **Pessoa 2:** depois de concluir RQ03/RQ04, mostrar as respectivas figuras finais, preferencialmente sem mais de uma troca de página.
5. **Pessoa 3:** mostrar as figuras finais de RQ05/RQ06 e terminar na conclusão consolidada.

Não abrir classes, funções, `.env`, token, checkpoint ou CSV durante a fala principal. Esses artefatos ficam apenas como evidência de apoio.

## Perguntas prováveis

### 1. Por que usar mediana?

A mediana é menos sensível a valores extremos. Isso é especialmente importante na RQ02, cuja distribuição tem forte cauda à direita e média muito acima do caso típico.

### 2. Por que GraphQL?

A API GraphQL permite solicitar, em uma mesma consulta, somente os campos necessários às seis questões. Isso reduz a necessidade de combinar várias respostas diferentes.

### 3. Por que 1.000 repositórios?

Esse foi o tamanho previsto pelo laboratório para ampliar a análise além da amostra inicial. Ele oferece diversidade suficiente para observar distribuições e casos extremos, sem significar que representa todo o GitHub.

### 4. Como os repositórios foram selecionados?

Usamos a busca `stars:>0 sort:stars-desc` e coletamos os mil primeiros resultados. Portanto, popularidade foi operacionalizada pelo número de estrelas no momento da coleta.

### 5. O que significa PR merged?

É uma pull request que foi incorporada ao repositório. A métrica usada é a quantidade acumulada por repositório.

### 6. Isso prova contribuição externa?

Não. Uma PR incorporada pode ser de integrante da própria equipe do projeto. A métrica indica atividade via pull requests, não a origem organizacional do autor.

### 7. Por que log1p no gráfico da RQ02?

A distribuição é muito assimétrica e possui valores muito altos. `log1p` torna o formato visual legível e aceita zeros; todas as estatísticas continuaram calculadas na escala original.

### 8. Os outliers foram removidos?

Não da análise oficial nem do CSV. A exclusão ocorreu somente em uma visão complementar de sensibilidade para comparar o quanto média e mediana dependiam dos extremos.

### 9. Por que IQR?

O IQR usa a metade central da distribuição e é robusto para dados assimétricos. Ele oferece um critério simples e reproduzível para identificar valores extremos.

### 10. O que a análise de robustez acrescentou?

Ela mostrou que a RQ01 é estável segundo o critério adotado e quantificou a sensibilidade da RQ02. A queda maior da média confirmou que a mediana descreve melhor o repositório típico.

### 11. Por que RQ01 foi considerada parcialmente confirmada?

A mediana de 7,7 anos sustenta maturidade elevada, mas a amostra inclui projetos de 2 dias e não existe um limiar formal ou grupo de comparação. Por isso, a conclusão não pode ser universal.

### 12. Quais são as principais limitações?

Estrelas são apenas uma proxy de popularidade; a coleta é um retrato temporal; PRs merged não provam contribuição externa; e linguagem principal e uso de Issues simplificam práticas diferentes entre comunidades.

### 13. Como garantiram que não havia duplicados?

O coletor compara o identificador `name_with_owner` antes de persistir e a validação final verificou unicidade. O CSV possui 1.000 registros, 1.000 identificadores únicos e zero duplicados.

### 14. O que aconteceria se a coleta fosse interrompida?

Cada página foi persistida incrementalmente e o cursor ficou salvo em checkpoint. A execução poderia ser retomada sem reiniciar a coleta e sem repetir repositórios já gravados.

### 15. Qual é a contribuição original do grupo?

A contribuição adicional foi a análise de robustez pelo critério IQR. Ela compara as medidas da amostra completa com uma visão sem extremos, sem modificar a análise oficial.

## Verificação antes do ensaio final

- Substituir todos os campos entre colchetes somente por resultados verificados.
- Recontar as palavras das Pessoas 2 e 3 após o preenchimento.
- Ensaiar com cronômetro e cortar detalhes antes de acelerar a fala.
- Manter a apresentação abaixo de 3min50s no ensaio para absorver pausas e transições.
