# Lab03 S02 — amostra-ouro e avaliação independente

Implementação das [#53](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/53),
[#54](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/54) e
[#57](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/57).
A rotulagem independente de Islayder (#54) foi importada e validada em
10/10/2026: 60/60 repositórios e 300/300 releases, sem erros. A #57 aguarda os
arquivos completos de Fernanda e Vinicius; concordância e consenso não foram
calculados nesta importação.

Fonte humana: `C:\Users\Islayder\Downloads\rotulacao_independente_60_repos.xlsx`,
aba `300 Releases`, conferida também contra o resumo `60 Repositórios`.
O alinhamento usou `repository` e tag exata, nunca posição de linha. Os valores
já estavam no schema oficial e foram copiados literalmente, incluindo 45
observações. Nenhum julgamento foi produzido ou reinterpretado automaticamente,
e nenhuma heurística corretiva foi usada. A planilha original foi preservada e
não foi adicionada ao Git. Hashes, integridade e contagens do CSV final estão em
[`islayder_import_manifest.json`](../data/validation/islayder_import_manifest.json).

## Fontes e sorteio

Dataset real: `data/processed/s02/`, separado do smoke. Consulte
`collection_manifest_s02.json`, `selection_funnel_s02.csv` e
`collection_audit_s02.json` para as contagens finais e a proveniência.
Janela UTC `[2025-10-01, 2026-10-01)`, definida pelo grupo em 10/10/2026.
As limitações da busca e da disponibilidade histórica estão em
[s02_collection.md](s02_collection.md).

O sorteio exige **pelo menos 300 elegíveis** depois dos filtros. O gerador
confere público, estrelas, Actions, branch/SHA, contagens e releases. Havendo
manifesto S02 junto das fontes, reaudita os runs e releases exportados e exige
as fontes canônicas e a mesma janela. Fixtures só são usadas nos testes.

Seed: **42**. Identidades são normalizadas com `casefold` e ordenadas antes de
`random.Random(42).sample(..., 60)`. Para cada repositório, a seed das releases
é o inteiro obtido de `SHA256("42:" + identidade_normalizada)`. O pool contém
apenas releases estáveis publicadas na janela e ancestrais do snapshot; é
ordenado por `(published_at UTC, release_id)` antes de sortear exatamente 5.
Não se substituem releases ausentes. Insuficiência bloqueia o sorteio e não
cria arquivos humanos. Manifesto registra exclusões e hashes SHA-256 das fontes.

```powershell
.\.venv\Scripts\python.exe -m src.s02_audit data/processed/s02
.\.venv\Scripts\python.exe -m src.s02 generate --repositories data/processed/s02/repositories_final_s02.csv --releases data/processed/s02/releases_s01.csv.gz --commits data/processed/s02/release_commits_s01.csv.gz --intervals data/processed/s02/release_intervals_s01.csv --start-date 2025-10-01 --end-date 2026-10-01 --seed 42
```

Os comandos são offline e não precisam de token. O gzip de commits contém o
CSV completo; a leitura conserva somente os commits dos itens sorteados em
memória, sem alterar a fonte. Campos grandes e quebras de linha são preservados.
Destinos existentes são recusados para proteger trabalho humano. Para outro
sorteio, informe outro `--output-dir` e outro `--report`.

## Arquivos para avaliação

- `data/gold_sample/gold_sample.csv`: contexto canônico, sem campos humanos.
- `data/gold_sample/gold_sample_islayder.csv`: arquivo individual de Islayder.
- `data/gold_sample/gold_sample_fernanda.csv`: arquivo individual de Fernanda.
- `data/gold_sample/gold_sample_vinicius.csv`: arquivo individual de Vinicius.
- `data/gold_sample/sampling_manifest.json`: algoritmo, fontes, seed e IDs.
- `reports/lab03_s02_islayder_review.md`: guia factual para revisão de Islayder.
- `reports/lab03_s02_islayder_review_selected_releases.txt`: lista completa,
  com repositórios, tags/nomes, datas e URLs para copiar.

Os três CSVs começam com o mesmo contexto e **todos os campos humanos vazios**,
mas são arquivos independentes. Não consulte os rótulos de outro avaliador nem
a previsão da heurística. Somente humanos preenchem `project_type`,
`releases_represent_real_delivery`, `corrective_release` e `notes`.

Cada linha identifica uma release por `item_id` e `release_id`. Os dois campos
de repositório devem repetir a mesma decisão nas suas cinco linhas, dentro do
arquivo do próprio avaliador. `corrective_release` é uma decisão por release.
`notes` é opcional e pode registrar evidências, dúvidas e casos mistos.

| Campo | Valor | Significado para a inspeção humana |
|---|---|---|
| project_type | library_framework | Biblioteca ou framework usado por outros programas |
| project_type | application_service | Aplicação ou serviço que entrega funcionalidade ao usuário |
| project_type | cli_tool | Ferramenta usada por interface de linha de comando |
| project_type | other | Tipo não representado pelas categorias anteriores |
| releases_represent_real_delivery | yes | As releases representam entregas reais ao usuário |
| releases_represent_real_delivery | no | As releases não representam entregas reais ao usuário |
| releases_represent_real_delivery | uncertain | Evidências insuficientes para decidir a representatividade |
| corrective_release | yes | O avaliador identifica a release como corretiva, com base nas evidências |
| corrective_release | no | O avaliador identifica a release como não corretiva |

As categorias são as solicitadas pelo grupo. Não foi criado um limiar
automático de predominância para releases com mudanças mistas. Dúvidas de
protocolo devem ser resolvidas pelos humanos e registradas, sem pedir à
heurística ou à IA para escolher o rótulo. `uncertain` só é aceito na dimensão
de representatividade; uma release sem decisão corretiva deve continuar vazia
até a revisão humana.

Preserve o contexto canônico, IDs, UTF-8, aspas e quebras de linha do CSV.
Edite somente os quatro campos humanos. O guia Markdown é auxiliar: o arquivo
que entra na validação é o CSV individual. Notes e mensagens de commits são
texto original da API. `interval_status`, `interval_error` e `commit_count`
descrevem disponibilidade factual, sem prever se uma release é corretiva.
README/commits URLs são atalhos de consulta, sem alegar conteúdo não coletado.

## Validar o preenchimento

```powershell
.\.venv\Scripts\python.exe -m src.s02 validate data/gold_sample/gold_sample_islayder.csv --json data/validation/islayder_validation.json
```

O resultado informa repositórios avaliados/faltantes, releases avaliadas/faltantes,
campos vazios, valores inválidos, duplicatas, itens ausentes/desalinhados,
contexto alterado e decisões inconsistentes nas cinco linhas de um repositório.
Ordem das linhas pode variar: o alinhamento usa IDs. Retorno 0 significa completo
e válido; 1 significa pendências/erros. Notes vazias não impedem conclusão.
No estado inicial, são 0/60 repositórios, 0/300 releases e 900 campos obrigatórios
vazios por avaliador. Isso é esperado e não equivale a respostas negativas.

## Concordância e consenso posteriores

Depois das três rotulagens completas:

```powershell
.\.venv\Scripts\python.exe -m src.s02 analyze
```

O comando valida os três arquivos independentes e os alinha pelo `item_id`.
Usa `statsmodels.stats.inter_rater.aggregate_raters` e `fleiss_kappa` sobre os
**votos originais**, antes do consenso. As dimensões são calculadas separadamente:
60 itens para tipo, 60 para representatividade e 300 para releases corretivas.
Uma única categoria observada torna Kappa indefinido; o valor fica vazio com
status explícito, sem substituir por 1 ou `NaN`.

Interpretação contínua, sem arredondar antes de categorizar: `<0` pobre;
`[0,0.20]` leve; `(0.20,0.40]` razoável; `(0.40,0.60]` moderada;
`(0.60,0.80]` substancial; `(0.80,1]` quase perfeita.

Saídas quando os três arquivos estão completos:

- `data/validation/fleiss_kappa.csv` e `analysis_status.json`.
- `reports/lab03_s02_validation.md`.
- `data/gold_sample/disagreements.csv`: divergências com votos originais.
- `data/gold_sample/consensus_votes.csv`: votos e resultado por dimensão.
- `data/gold_sample/manual_resolutions_template.csv`: casos sem maioria, vazios.
- `data/gold_sample/gold_sample_consensus.csv`: somente após resolver todos os casos.

Três votos iguais geram consenso direto. Dois votos iguais geram maioria simples.
Três votos diferentes exigem revisão humana; o consenso continua vazio.
Copie o template para `data/gold_sample/manual_resolutions.csv` e preencha apenas
os casos solicitados, com `consensus`, `reviewer` e justificativa em `notes`.

```powershell
.\.venv\Scripts\python.exe -m src.s02 analyze --resolutions data/gold_sample/manual_resolutions.csv --output-dir data/validation/resolved --consensus-dir data/gold_sample/resolved --report reports/lab03_s02_validation_resolved.md
```

Use pastas novas para preservar resultados anteriores; saídas nunca sobrescrevem
entradas ou rótulos originais. Retornos: 0 concluído; 1 aguardando avaliações;
2 aguardando revisão manual. Enquanto faltam rótulos, o comando só produz
diagnósticos e relatório de espera: não escreve Kappa, divergências ou consenso.
A execução inicial usa `data/validation/awaiting_labels/`, deixando o destino
padrão disponível para a primeira análise humana completa.

## Verificação

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=src --cov-report=term-missing --cov-fail-under=96
```

O piso de cobertura considera a linha de base integral de 96% da branch.
Testes cobrem sorteio determinístico, gate de 300, 60×5, contexto cego,
independência, gzip/campos grandes, categorias, incompletude, IDs/alinhamento,
Kappa conhecido (1/3), categoria constante, maioria, unanimidade e revisão manual.
Nenhuma fixture de votos é usada nos arquivos reais.
