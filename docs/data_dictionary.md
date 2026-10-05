# Dicionário de dados — Fernanda, Lab03S01

CSVs UTF-8, vírgula, cabeçalhos estáveis; mensagens multilinha/aspas escapadas
pelo módulo `csv`. Booleanos: `True`/`False`. Vazio é ausente/não medido, nunca
zero. Timestamps ISO preservam o fuso da API; cálculos/filtros são em UTC.
Janela com fim exclusivo. `full_name` (texto `owner/repo`) aparece em todos os
arquivos e identifica o repositório. SHAs e URLs são texto.

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
