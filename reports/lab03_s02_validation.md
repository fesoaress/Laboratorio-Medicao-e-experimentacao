# Lab03 S02 — validação humana

- Islayder: **60/60 repositórios; 300/300 releases; zero erros ou campos obrigatórios vazios**.
- Fernanda e Vinicius: aguardando os arquivos completos, conforme informado pelo usuário.

Em 10/10/2026, a rotulagem humana independente de Islayder foi importada da
planilha `rotulacao_independente_60_repos.xlsx`, sem alterar decisões. O arquivo
oficial foi alinhado por repositório/tag à amostra #53; os campos factuais e
as 45 observações humanas foram preservados. Valores já estavam no schema:
nenhuma normalização foi necessária. A #54 está tecnicamente concluída.

Contagens diretamente do CSV final:

| Dimensão | Categoria | Quantidade | Unidade |
|---|---|---:|---|
| project_type | library_framework | 23 | repositórios |
| project_type | application_service | 25 | repositórios |
| project_type | cli_tool | 10 | repositórios |
| project_type | other | 2 | repositórios |
| releases_represent_real_delivery | yes | 59 | repositórios |
| releases_represent_real_delivery | no | 1 | repositórios |
| releases_represent_real_delivery | uncertain | 0 | repositórios |
| corrective_release | yes | 99 | releases |
| corrective_release | no | 201 | releases |

Validador oficial: código 0; detalhes em
[`islayder_validation.json`](../data/validation/islayder_validation.json).
A proveniência e hashes estão em
[`islayder_import_manifest.json`](../data/validation/islayder_import_manifest.json).

Nenhuma heurística foi utilizada para produzir rótulos. As avaliações de
Fernanda e Vinicius não foram consultadas nem modificadas. A #57 permanece
aguardando esses dois arquivos completos: nenhum Kappa, consenso, precisão,
recall ou F1 foi calculado. O arquivo `awaiting_labels/analysis_status.json`
conserva o diagnóstico histórico da geração inicial, anterior à importação.
