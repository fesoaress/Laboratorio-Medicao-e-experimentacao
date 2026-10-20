# Processo e participação — Lab03S03

Branch exclusiva: `Laboratorio-3`. HEAD inicial local
`0fb56f6133ddfa0b47bbe93415c90ac767ead396`; `main` observada em
`07df90fc3a418c4a149b30ba6dd1a151bf396b8b`. Não houve integração com main.
Os cinco commits S02 foram auditados e publicados por push normal.

CI S02 confirmado: [run 39478984728](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/actions/runs/39478984728),
SHA `0fb56f6133ddfa0b47bbe93415c90ac767ead396`, job `testes`
118822284052: 523 testes, 97,97%, threshold 96%, sucesso. Essa evidência
pertence à S02; a evidência S03 é registrada na auditoria final da S03.

## Issues reais criadas

| Issue | Escopo |
|---|---|
| #61 | Auditoria independente S02/dataset |
| #62 | Descrição RQ01–04 |
| #63 | Classificação DORA |
| #64 | Spearman RQ05 |
| #65 | Fatores, Holm e efeitos RQ06 |
| #66 | Sensibilidade e coleta pontual RQ07 |
| #67 | Inovação por bootstrap |
| #68 | Retrabalho RQ08 |
| #69 | Gráficos e tabelas |
| #70 | Resultados do artigo |
| #71 | Discussão e ameaças à validade |
| #72 | Integração, reprodutibilidade, testes e CI |
| #73 | Participação individual e Projects |

Base dos links: `https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/`.
As Issues têm objetivos, critérios verificáveis, artefatos e dependências.
Permanecem sem responsável atribuído automaticamente: não foi encontrada
distribuição humana confirmada para as novas tarefas. A #66 registra a
decisão humana de preservar C1/C2/C3 e coletar os intervalos faltantes.

## GitHub Projects — ação humana necessária

A consulta GraphQL dos Projects do usuário autenticado retornou `FORBIDDEN`,
`Resource not accessible by personal access token`. A lista vinculada ao
repositório veio vazia. Isso não demonstra inexistência do board do grupo.
Não foi criado outro Projects e não foi inventado seu WIP ou seu estado.

Um integrante com acesso deve abrir o Projects já utilizado pelo grupo,
adicionar #61–#73, conferir o limite WIP vigente e os itens efetivamente
em andamento, vincular os responsáveis após confirmação e mover cada item
segundo suas evidências de implementação/revisão/CI. A #73 deve permanecer
pendente até comprovar essas ações e a contribuição individual. Não se
deve mover todas as tarefas para concluído apenas pela existência dos arquivos.

## Autoria e requisito individual

A implementação desta execução é assistida e centralizada. Ela não comprova
que Fernanda, Vinicius e Islayder produziram, individualmente, um artefato
de código da S03. O grupo deve dividir e registrar contribuições reais de
código, respectivas revisões e commits. Não serão produzidos commits com
autoria alheia nem coautorias presumidas. A evidência de participação humana
é pendência de processo separada da validação técnica das análises.

## Publicação e CI S03 verificados

O código e os resultados em `7aa3620fb819fd5e2abb3d98718678685abdc922`
foram publicados com push normal na `Laboratorio-3`.
[CI 39486894538](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/actions/runs/39486894538):
584 testes aprovados, cobertura 96,97%, mínimo 96% mantido, Python 3.12.15,
conclusão `success`. O manifesto de publicação está em `ci_s03.json`.

O primeiro CI detectou referência a três expansões CSV locais ignoradas.
A correção restringiu a proveniência às fontes gzip versionadas e adicionou
um teste de regressão. Nenhuma métrica ou figura mudou. Uma exportação limpa
do Git executou o pipeline completo sem `.env`, cache bruto ou esses CSVs,
reproduzindo as 18 tabelas e 27 imagens byte a byte; nove testes de auditoria
e integridade também passaram nessa exportação.

As Issues técnicas #61–#72 foram fechadas com essas evidências. A #73
permanece aberta pelas ações humanas descritas acima. Commits documentais
posteriores registram a evidência sem alterar o código ou os dados analisados.
