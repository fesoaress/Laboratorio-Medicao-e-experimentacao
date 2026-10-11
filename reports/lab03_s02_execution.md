# Lab03 S02 — execução real

Atualização de 10/10/2026: a rotulagem humana independente de Islayder foi
importada da planilha fornecida e validada (60/60 repositórios, 300/300 releases,
zero erros). A #54 está tecnicamente concluída. A #57 aguarda Fernanda e
Vinicius. Consulte [lab03_s02_validation.md](lab03_s02_validation.md).
Os resultados de campos vazios abaixo descrevem a geração inicial, anterior
à importação; seu diagnóstico histórico permanece preservado.

Branch: `Laboratorio-3`. Coleta finalizada em 10/10/2026, sem push.
Janela UTC: **[2025-10-01, 2026-10-01)**, com fim exclusivo, definida pelo grupo.

Foram processados **1.782 candidatos únicos**: **311 elegíveis**, 1.469
descartados e dois sem comprovação por erro de API. Portanto,
**final_sample = 311 >= 300**. A amostra final contém 27.152 releases estáveis
na janela e 494.200 workflow runs observados, dos quais 454.382 válidos.
O smoke permanece em diretório separado.

## Funil auditável

| Etapa | Aprovações comprovadas | Reprovados nesta etapa | Não medidos nesta etapa |
|---|---:|---:|---:|
| Candidatos processados | 1.782 | 0 | 0 |
| Públicos | 1.782 | 0 | 0 |
| Default branch identificada | 1.782 | 0 | 0 |
| GitHub Actions | 741 | 207 | 834 |
| Pelo menos 5 releases estáveis publicadas | 493 | 248 | 0 |
| Pelo menos 5 releases estáveis ancestrais | 379 | 72 | 42 |
| Pelo menos 50 runs válidos | 311 | 67 | 1 |
| Amostra final | 311 | 1.469 no total | 2 candidatos não resolvidos |

O funil apresenta as aprovações comprovadas entre os sobreviventes da etapa
anterior. A otimização por releases reprovou candidatos antes de medir Actions;
por isso, 834 não medidos nessa etapa não significam ausência de Actions nem
834 candidatos ainda pendentes. Tentativas iniciais também verificaram runs
antes da ancestralidade de releases. Os descartes definitivos foram: 1.154
por releases insuficientes, 207 por ausência de Actions e 108 por runs
insuficientes. Estrelas > 1.000 e referência/SHA válido foram conferidos para
todos os elegíveis, assim como todos os demais critérios do pipeline.

`Azure/azure-sdk-for-net` ficou fora da amostra porque a contagem de runs
mudou durante a paginação; `shuakami/qq-chat-exporter` ficou fora por HTTP 422
ao resolver uma tag. Cache, checkpoints e histórico das retomadas ficam
localmente em `data/raw/s02/`, ignorados pelo Git.

## Fontes e contexto

Dataset: [data/processed/s02](../data/processed/s02/).
Consulte o [manifesto](../data/processed/s02/collection_manifest_s02.json),
o [funil](../data/processed/s02/selection_funnel_s02.csv), a
[auditoria](../data/processed/s02/collection_audit_s02.json) e o
[manifesto de arquivos comprimidos](../data/processed/s02/archive_manifest_s02.json).
A auditoria final aprovou 311 repositórios sem contradições nas fontes.
Os gzip preservam integralmente os CSVs; seus hashes descomprimidos foram
conferidos contra os originais. Os arquivos CSV grandes continuam disponíveis
localmente e são ignorados pelo Git; seus snapshots gzip são versionados.

O enriquecimento cobriu todos os 311 elegíveis: 261 com status `complete`,
29 com `comparison_error` e 21 com `metric_error`. Essas exceções preservam os
fatos disponíveis e as métricas ausentes; não criam novos critérios de exclusão.
O contexto do WPT usa objetos Git completos e verificou 69.734 refs de tags.
As limitações de busca, disponibilidade histórica e comparações constam em
[s02_collection.md](../docs/s02_collection.md).

## Amostra-ouro e validação

Seed **42**: exatamente **60 repositórios e 300 releases reais**, cinco por
repositório. Não houve exclusão adicional no sorteio.
O [manifesto do sorteio](../data/gold_sample/sampling_manifest.json) registra
algoritmo, IDs e hashes das fontes.

- [CSV de Islayder](../data/gold_sample/gold_sample_islayder.csv).
- [CSV de Fernanda](../data/gold_sample/gold_sample_fernanda.csv).
- [CSV de Vinicius](../data/gold_sample/gold_sample_vinicius.csv).
- [Guia factual de revisão](lab03_s02_islayder_review.md).
- [Lista completa dos 60 × 5](lab03_s02_islayder_review_selected_releases.txt).

Os três CSVs iniciam com contexto idêntico e todos os quatro campos humanos
vazios. Não houve classificação, sugestão de rótulos ou execução da heurística
corretiva. Notes, mensagens e links estão nos CSVs e no guia factual.
Há três releases sem body disponível, 21 sem commits listados e um repositório
sem descrição; URLs e status factuais permitem consulta sem inventar conteúdo.

O validador real terminou com código 1, esperado: 0/60 repositórios avaliados,
0/300 releases avaliadas e 900 campos obrigatórios vazios por avaliador.
Os [diagnósticos individuais](../data/validation/islayder_validation.json)
e o [estado de espera](../data/validation/awaiting_labels/analysis_status.json)
preservam os detalhes. A análise também terminou com código 1, aguardando as
três avaliações; nenhum valor de Kappa, divergência ou consenso foi gerado.

## Verificação e pendências

Suíte integral: **407 testes aprovados**. Cobertura: **97,70%**
(2.468/2.526 instruções), acima da linha de base de **95,72%**. Testes incluem
amostragem, integridade dos avaliadores, campos grandes/gzip, paginação,
retomada, objetos Git reais em fixture sintética local, Kappa conhecido e
consenso. Fixtures de testes não foram usadas na coleta real.

As Issues #53, #54 e #57 têm commits locais vinculados por número.
A #54 foi concluída após a importação humana descrita na atualização inicial;
Kappa e consenso empíricos aguardam Fernanda e Vinicius. Instruções e comandos de
validação/análise estão em [s02_validation.md](../docs/s02_validation.md).
Não houve push. A coleta e o contexto terminaram; o token temporário pode ser
revogado pelo usuário. `.env` e dados brutos não são versionados.
