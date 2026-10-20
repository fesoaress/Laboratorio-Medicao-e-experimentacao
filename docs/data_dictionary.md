# Dicionário de dados — Fernanda, Lab03 S01/S02

CSVs UTF-8, vírgula, cabeçalhos estáveis; mensagens multilinha/aspas escapadas
pelo módulo `csv`. Booleanos: `True`/`False`. Vazio é ausente/não medido, nunca
zero. Timestamps ISO preservam o fuso da API; cálculos/filtros são em UTC.
Janela com fim exclusivo. `full_name` (texto `owner/repo`) identifica o
repositório nos arquivos S01. Na amostra-ouro, o nome é `repository`.
SHAs e URLs são texto.

## releases_s01.csv

Histórico publicado ancestral da default branch e anterior ao fim da janela,
inclusive predecessoras antigas e pré-releases.

- `release_id`: inteiro, `release.id`.
- `tag_name`: texto, `release.tag_name`.
- `published_at`: timestamp, `release.published_at`; proxy de entrega.
- `commit_sha`: SHA resolvido por `/commits/{tag_name}`.
- `prerelease`: booleano da API; True exclui da referência principal.
- `html_url`: URL da release, campo original da API.
- `target_commitish`: texto da API, sem valor probatório de branch.
- `in_window`: booleano, `início <= published_at < fim`.

## tags_s01.csv

Todas as tags, inclusive sem release. Variante de tags exige ambas as flags True.

- `name`: texto, `tag.name`.
- `commit_sha`: `tag.commit.sha`.
- `author_date`: timestamp, `commit.author.date` do SHA apontado.
- `on_default_branch`: booleano, `ahead`/`identical` da comparação
  `tag_sha...default_branch_sha`; SHA igual ao snapshot também é válido.
- `in_window`: booleano, `início <= author_date < fim`.

## excluded_releases_s01.csv

- `release_id`: inteiro, ID da release excluída.
- `tag_name`: texto, nome original, se disponível.
- `reason`: texto, `draft`, `outside_window_after_end` ou `not_on_default_branch`.
  Pré-releases são preservadas no histórico, não entram neste arquivo de descartes.

## release_intervals_s01.csv

Uma linha por release estável na janela, inclusive intervalos vazios/erro.

- `release_id`, `tag_name`: inteiro/texto, identificadores da release atual.
- `previous_release_id`: inteiro/ausente, ID da release estável anterior.
- `previous_tag_name`: texto/ausente, tag anterior.
- `base_sha`, `head_sha`: SHAs da predecessora e da release atual.
- `commit_count`: inteiro/ausente, SHAs novos únicos; 0 para intervalo completo
  vazio, ausente para erro ou ausência de predecessora.
- `status`: texto, `complete`, `no_previous_release`, `ignored_compare_404` ou `error`.
- `error_detail`: texto/ausente, diagnóstico sem credenciais.
- `error_status`: inteiro/ausente, código HTTP retornado na comparação; 404
  indica a exclusão da release do Lead Time segundo a FAQ.

## release_commits_s01.csv

Uma linha por SHA único em cada intervalo completo, sem recorte pela data do commit.

- `release_id`, `tag_name`: inteiro/texto, release que entrega a mudança.
- `sha`: `commit.sha`.
- `author_date`: timestamp, `commit.author.date`; utilizado no Lead Time.
- `committer_date`: timestamp, `commit.committer.date`; preservado para auditoria.
- `message`: texto, `commit.message`, pode conter quebras de linha.
- `html_url`: URL, `commit.html_url`.

## lead_time_releases_s01.csv

Observações dos intervalos válidos, ignorando comparações HTTP 404 conforme a FAQ.
Release inicial, sem novos commits ou ignorada por 404 não gera observação.
Outros erros de comparação mantêm o resultado do repositório indisponível.

- `release_id`, `tag_name`: inteiro/texto, release medida.
- `commit_count`: inteiro, commits novos únicos.
- `lead_time_hours`: real, diferença em segundos entre `published_at` e menor
  `author_date`, dividida por 3600.

## lead_time_commits_s01.csv

- `release_id`, `tag_name`: inteiro/texto, release que entrega o commit.
- `commit_sha`: SHA da observação.
- `lead_time_hours`: real, `(published_at − author_date).total_seconds()/3600`.
  SHA repetido no intervalo conta uma vez; observações em releases distintas
  são preservadas conforme RQ02(b).

## lead_time_s01.csv

Uma linha por repositório solicitado, inclusive erros/pendências.

- `start_date`, `end_date`: datas ISO da janela; fim exclusivo.
- `default_branch`: texto, branch informada pela API.
- `default_branch_sha`: SHA/ausente, snapshot usado para ancestralidade.
- `release_count`: inteiro/ausente, releases da janela, sem draft/prerelease,
  ancestrais da branch; usado no critério de pelo menos 5 releases do funil.
- `prerelease_count`: inteiro/ausente, pré-releases da janela ancestrais da branch.
- `tag_count`: inteiro/ausente, tags na janela e ancestrais da branch.
- `status`: texto, `pending_collection`, `complete`, `api_error`, `data_error`,
  `comparison_error` ou `metric_error`. Complete pode ter zero observações.
- `error_detail`: texto/ausente, diagnóstico sem credenciais.
- `releases_without_predecessor`: inteiro/ausente, primeiras releases ignoradas.
- `releases_without_new_commits`: inteiro/ausente, intervalos completos vazios.
- `releases_ignored_compare_404`: inteiro/ausente, releases da janela excluídas
  apenas do Lead Time por HTTP 404 no compare; não reduz `release_count`.
- `lead_time_release_count`: inteiro/ausente, número de observações RQ02(a).
- `lead_time_release_median_hours`: real/ausente, mediana das durações RQ02(a).
- `lead_time_release_q1_hours`, `lead_time_release_q3_hours`: reais/ausentes,
  quartis 25%/75% das durações RQ02(a).
- `lead_time_release_iqr_hours`: real/ausente, Q3 menos Q1 em RQ02(a).
- `lead_time_commit_count`: inteiro/ausente, número de observações RQ02(b).
- `lead_time_commit_median_hours`: real/ausente, mediana de todos os commits/releases.
- `lead_time_commit_q1_hours`, `lead_time_commit_q3_hours`: reais/ausentes,
  quartis 25%/75% das durações RQ02(b).
- `lead_time_commit_iqr_hours`: real/ausente, Q3 menos Q1 em RQ02(b).

Quartis usam interpolação linear na posição `(n−1)×p`, tipo 7. Uma observação:
Q1=Q3=mediana, IQR=0. Sem observações: count=0, estatísticas vazias. Com erro não 404:
contagens/estatísticas de Lead Time ficam ausentes. Contagem de releases concluída
pode continuar conhecida após falha nos commits. Duração negativa nunca vira zero.

## release_validation_s01.csv

Compatível com `src.funnel.load_evidence` e `--validation-csv`.

- `start_date`, `end_date`: datas ISO da mesma janela oficial usada na coleta.
- `release_count`: inteiro/ausente, contagem principal descrita acima.
- `valid_workflow_runs`: inteiro/ausente, sempre ausente nesta contribuição;
  preenchimento compete ao coletor de Vinicius.

## delivery_manifest_s01.json

- `collected_at`: timestamp UTC do início da execução.
- `window`: objeto com `start_date`/`end_date`.
- `per_page`: inteiro, tamanho solicitado das páginas.
- `definition`: texto, regra principal de inclusão de releases.
- `tag_date_source`: texto, `commit.author.date`.
- `unit`: texto, `hours`.
- `quartiles`: texto, `linear_interpolation_type_7`.
- `releases_ignored_compare_404`: inteiro, soma dos casos 404 registrados nos
  repositórios processados; linhas pendentes ainda não foram medidas.
- `repositories`: lista com os mesmos campos de `lead_time_s01.csv`, tipos JSON
  nativos e `null` para ausências; registra o snapshot de branch de cada repo.

CSVs de seleção/metadados preservam o contrato de Islayder em
`src.pipeline.REPOSITORY_FIELDS` e `src.funnel.FUNNEL_FIELDS`.
Novos componentes atualizam apenas evidência de releases, sem fabricar runs.

## S02 — rotulagem humana de Fernanda (#55)

O contrato cego completo está em `src.gold_sample.CONTEXT_FIELDS`; o protocolo
e as categorias estão em [s02_validation.md](s02_validation.md). Contexto e
identidade nunca são editados pelo formulário. `gold_sample_fernanda.csv` contém
300 linhas, com exatamente as cinco releases sorteadas de cada um dos 60 projetos.

- `item_id`: texto, `repository.casefold() + "::release::" + release_id`; chave
  de alinhamento independente da posição da linha.
- `project_type`: categoria humana `library_framework`, `application_service`,
  `cli_tool` ou `other`; mesma resposta nas cinco linhas do projeto.
- `releases_represent_real_delivery`: categoria humana `yes`, `no` ou `uncertain`;
  mesma resposta nas cinco linhas do projeto.
- `corrective_release`: categoria humana `yes` ou `no`, uma por release.
- `notes`: texto opcional, observações/evidências humanas; aceita multilinha.

Vazio nos três campos categóricos significa **não avaliado**, nunca `no`.
São 420 decisões independentes, representadas em 900 células obrigatórias pela
repetição dos rótulos de projeto. `gold_sample_consensus.csv` posterior usa o
mesmo contrato, com os rótulos consolidados na #57.

## S02 — predictions.csv (#58)

Arquivo derivado, gerado somente após a rotulagem de Fernanda e o consenso.
Jamais é entrada/sugestão para a revisão independente. Uma linha por release
da amostra-ouro; não representa o dataset completo dos 311 repositórios.

- `item_id`, `repository`, `release_id`, `tag_name`: identidades da amostra.
- `previous_tag`: tag da release estável imediatamente anterior no histórico
  completo; vazio quando não há predecessor disponível.
- `consensus`: rótulo corretivo humano consolidado (`yes`/`no`).
- `version`: versão explícita da política (`v1` a `v5`); v5 foi aceita.
- `corrective_release`: **previsão automática** `yes`/`no`, distinta do campo
  humano de mesmo nome no CSV individual. Consulte o caminho do arquivo.
- `reason`: texto, regra que determinou a decisão; descrita em `corrective.py`.
- `patch_only`: booleano, major/minor iguais e patch estritamente maior.
- `correction_commits`, `feature_commits`: inteiros, assuntos de commits com
  sinais lexicais segundo a versão. Um assunto misto pode entrar em ambos.
- `correction_notes`, `feature_notes`: inteiros, entradas nas notes com sinais;
  cabeçalhos só contextualizam as listas, sem contar como mudanças.
- `commit_context_complete`: booleano, `interval_status == "complete"`;
  False registra contexto parcial/indisponível, não ausência de correções.

## S02 — evaluation.json e histórico da heurística

- `items`: inteiro, 300 pares alinhados nesta amostra.
- `positive_label`: `yes`.
- `tp`, `fp`, `fn`, `tn`: inteiros da matriz de confusão.
- `precision`, `recall`, `f1`: reais em [0,1], calculados com scikit-learn;
  `zero_division=0` produz zero computacional em denominadores nulos.
- `precision_defined`, `recall_defined`, `f1_defined`: booleanos; devem ser
  consultados antes de interpretar zeros como resultados empíricos definidos.
- `threshold`: 0,70, aplicado a F1 sem arredondamento.
- `status`: `accepted`, `needs_refinement` ou
  `unassessable_no_positive_consensus`.
- `version`, `policy`: identificador e descrição da regra avaliada.
- `sources`: caminhos/SHA-256 da amostra, próprio CSV, consenso e dois históricos.
- `evaluated_at`: timestamp UTC da avaliação.
- `python`, `sklearn`: versões do ambiente.
- `implementation_sha256`: SHA-256 de `corrective.py.txt`, preservado na execução.
- `predictions_sha256`: SHA-256 do CSV derivado.
- `incomplete_commit_context`: número de releases cujo intervalo não é completo.
- `limitations`: lista de limitações metodológicas explícitas.

Cada execução usa uma pasta nova para conservar resultados, código e fontes de
cada versão. Não há arquivos de resultados empíricos da #58 enquanto o consenso
estiver ausente. O status do classificador não substitui o fechamento do dataset
final, a integração das variantes DORA ou o relatório de concordância.

## S02 — dataset_final_s02.csv (#51)

Uma linha por repositório elegível da amostra final (311 linhas). Merge por
`full_name` a partir de `repositories_final_s02.csv`, com left join nas fontes
de métricas. Colunas de variante são nomeadas explicitamente para evitar
ambiguidade entre definições operacionais.

### Metadados (origem: repositories_final_s02.csv)

- `repository_id`: inteiro, `repository.id`.
- `full_name`, `owner`, `name`: texto, identidade GitHub.
- `html_url`: URL do repositório.
- `stargazers_count`: inteiro, contagem no `collected_at`.
- `language`: texto, linguagem principal detectada pela API.
- `created_at`: timestamp, data de criação.
- `repo_age_days`: inteiro, dias entre `created_at` e `collected_at`.
- `default_branch`: texto, branch principal.
- `contributors_count`: inteiro, contagem via API.
- `has_github_actions`: booleano, sinaliza fluxo de CI.
- `collected_at`: timestamp UTC da coleta de metadados.
- `release_count`: inteiro, releases estáveis na janela.
- `valid_workflow_runs`: inteiro, runs com status classificável na janela.
- `metadata_complete`: booleano, metadados coletados sem erro.
- `status`: texto, `selected` (reprovado no funil ficou fora).
- `reasons`: texto, motivos do estado final.
- `description`: texto, descrição pública do repositório.

### Deployment Frequency — RQ01 (origem: deployment_frequency_s02.csv)

- `deployment_frequency_releases`: inteiro, releases estáveis na janela.
  Mesmo valor que `release_count`, repetido para preservar variante.
- `deployment_frequency_window_days`: real, duração da janela em dias (365.0).
- `deployment_frequency_per_week`: real, `releases / (window_days/7)`.
- `deployment_frequency_per_month`: real, `releases / (window_days/30)`.

### Lead Time for Changes — RQ02 (origem: lead_time_s01.csv)

Variante (a) — por release:

- `lead_time_release_count`: inteiro, observações de RQ02(a).
- `lead_time_release_median_hours`: real/ausente, mediana.
- `lead_time_release_q1_hours`, `lead_time_release_q3_hours`: reais/ausentes.
- `lead_time_release_iqr_hours`: real/ausente, Q3 − Q1.

Variante (b) — por commit:

- `lead_time_commit_count`: inteiro, observações de RQ02(b).
- `lead_time_commit_median_hours`: real/ausente, mediana.
- `lead_time_commit_q1_hours`, `lead_time_commit_q3_hours`: reais/ausentes.
- `lead_time_commit_iqr_hours`: real/ausente, Q3 − Q1.

Diagnóstico:

- `lead_time_window_start`, `lead_time_window_end`: datas ISO da janela.
- `lead_time_releases_without_predecessor`: inteiro, primeiras releases ignoradas.
- `lead_time_releases_without_new_commits`: inteiro, intervalos completos vazios.
- `lead_time_releases_ignored_compare_404`: inteiro, releases excluídas apenas
  do Lead Time por 404 no compare; não reduz `release_count`.

Quartis: interpolação linear em `(n−1)×p`, tipo 7. Sem observações:
count=0 e estatísticas vazias. Duração negativa nunca vira zero.

### Change Failure Rate — RQ03 (origem: workflow_metrics_s02.csv)

Variante (a) — CI:

- `cfr_ci_successes`: inteiro, workflow runs com status `success`.
- `cfr_ci_failures`: inteiro, workflow runs com status `failure`.
- `cfr_ci_ignored`: inteiro, runs sem status classificável (não entram na razão).
- `cfr_ci`: real/ausente, `failures / (failures + successes)`;
  ausente quando denominador é zero.

Variante (b) — entrega:

- `cfr_delivery`: real/ausente, `failed_releases/evaluable_releases`, com a
  política `any_corrective_7d_v1` e a heurística v5 validada. Há 311 válidos e
  zero ausentes. O numerador conta originais seguidos por qualquer corretiva
  em até sete dias, não o número de corretivas. Releases intermediárias não
  impedem evidência. A antiga razão direta do consenso amostral era provisória
  e não foi usada no cálculo final.
- `cfr_delivery_source`: texto, caminho do manifesto, política, versão e SHA-256
  da avaliação usada. Presente nos 311 repositórios. Denominador nulo seria
  ausência, nunca zero imputado.

### Recovery Time — RQ04 (origem: workflow_metrics_s02.csv)

- `recovery_time_n_episodes`: inteiro, total de episódios de falha observados.
- `recovery_time_n_censored`: inteiro, episódios sem retorno a sucesso na janela.
- `recovery_time_median_hours`: real/ausente, mediana dos episódios resolvidos;
  censurados não entram na mediana.
- `recovery_time_censored_proportion`: real/ausente, `n_censored / n_episodes`;
  ausente quando não há episódios.

Episódios individuais ficam em `recovery_episodes_s02.csv` (uma linha por
episódio, identificado também por `workflow_id`), com `failure_started_at`,
`recovered_at` e `hours`.

### Convenções

- Vazio é ausente/não medido, nunca zero. `0` em contagens é valor real.
- Frações (`cfr_*`, `censored_proportion`) em [0,1].
- Durações em horas decimais.
- `full_name` é a chave de merge entre todas as fontes desta seção.

## S02 — auditoria e consenso em 20/10/2026

`data/validation/dataset_metrics_audit.json` registra população, número de
colunas, duplicatas, perfil `valid/missing/invalid` por campo numérico,
motivos dos ausentes, erros de consistência e caminhos/SHA-256 das fontes.
Audita fontes, tipos, domínios, frequências, CFR(a/b), quartis/IQR e denominadores
de censura. Estado final: `valid`. A auditoria anterior à inclusão de CFR(b)
está preservada em `pre_manual/dataset_metrics_audit_before_cfr.json`.

`data/validation/fleiss_kappa.csv` contém as três dimensões sobre votos
originais (60/60/300 itens). `analysis_status.json` registra a completude e os
hashes dos três avaliadores e zero casos pendentes. `consensus_votes.csv`
contém 420 decisões distintas, com `needs_manual_review=False`;
`disagreements.csv` preserva 70 divergências originais. O template manual tem
uma linha original vazia, preservada para auditoria; a decisão humana está
em `manual_resolutions.csv`. `gold_sample_consensus.csv` está completo, com
60 repositórios e 300 releases. Os diretórios `pre_manual/` preservam a
primeira análise antes da decisão humana.

## S02 — população corretiva e CFR(b)

- `corrective_v5/release_predictions.csv`: 27.152 previsões factuais do
  classificador validado, uma por release. `classification_usable=False` em
  180 casos indica contexto insuficiente; a previsão binária bruta não deve
  ser tratada como evidência negativa nesses casos. `manifest.json` registra
  hashes, fontes e a avaliação aceita.
- `cfr_delivery_releases_s02.csv`: `status` é `failed` (20.038), `not_failed`
  (6.406), `right_censored` (677) ou `unassessable_context` (31). `failed`
  fica vazio nos dois últimos estados. `evidence_release_id/evidence_tag`
  identifica a primeira corretiva posterior utilizável até R+7d, quando existe.
  `unavailable_posterior_classifications` conta classificações insuficientes
  nesse intervalo; uma positiva conhecida basta para demonstrar existência.
- `cfr_delivery_s02.csv`: agregação por repo; `failed_releases`,
  `evaluable_releases`, `right_censored`, `unassessable_context`, razão,
  `status` e `source`. Denominador global: 26.444 originais avaliáveis.
- `cfr_delivery_manifest_s02.json`: definição confirmada pelo grupo,
  cutoff `2026-09-24T00:00:00+00:00`, versão, hashes da avaliação/população,
  totais e hashes das duas saídas.

Originais nos últimos sete dias são excluídos incondicionalmente, mesmo com
corretiva observada; ainda podem ser evidência para anteriores. Não ter
predecessora não exclui o original. Sem positiva conhecida, classificação
posterior indisponível torna o original não calculável e fora do denominador.
Somente eventos estáveis dentro da janela entram no cálculo. As regras
completas e os casos de borda estão em `cfr_delivery_policy.md`.
