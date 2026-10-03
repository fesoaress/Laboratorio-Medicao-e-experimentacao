# Auditoria da consolidação

Esta proposta organiza os estados finais dos três laboratórios na branch
`repo-consolidation`. A `main` permanece em `c4aa604ed55eec6d43a9cb5a7e126237cd1a58c2`
até a revisão e o merge do PR. Nenhuma branch foi apagada; não houve force push,
reescrita de histórico ou regeneração de resultados científicos.

## Fontes e ancestralidade

| Branch fonte | HEAD confirmado | Merge-base com a main inicial | Commits exclusivos frente à main inicial | Preservação |
| --- | --- | --- | ---: | --- |
| main | c4aa604ed55eec6d43a9cb5a7e126237cd1a58c2 | c4aa604ed55eec6d43a9cb5a7e126237cd1a58c2 | 0 | Ancestral da consolidação |
| Laboratório-1 | 4133fa3cbb47a2ba751e66f6399e948a421c4450 | 4133fa3cbb47a2ba751e66f6399e948a421c4450 | 0 | Estado final completo em lab01/ |
| Laboratorio-2 | 489577a7a0aaca272737464c555acef823f82cd7 | 0ddd5e18cad171fda09e554ec800ccd3ff210675 | 4 | Conteúdo próprio em lab02/; regras globais em .gitignore |
| Laboratorio-3 | 3abe79b88e011bad057b4155fa56fa943c11f6f2 | 3abe79b88e011bad057b4155fa56fa943c11f6f2 | 0 | Todos os arquivos de lab03/ preservados |
| vinicius | 3b0e0b9655442553fa95b015c52164113d738e5b | 3b0e0b9655442553fa95b015c52164113d738e5b | 0 | Histórico integral como ancestral; versões posteriores do Lab01 são canônicas |
| repo-consolidation | HEAD desta branch | c4aa604ed55eec6d43a9cb5a7e126237cd1a58c2 | 8 ao concluir os quatro commits estruturais | Estados finais dos três laboratórios |

O comando `python .github/consolidation/audit.py --branches` exibe os HEADs
completos atuais das seis branches, merge-bases, contagens e ancestralidade.
O próprio HEAD da consolidação não é gravado neste arquivo para evitar uma
referência circular ao commit que contém a auditoria.

O merge real `18a846f42c2ef135c4a8b76e6672b56b9f483e6a` incorporou o HEAD final
do Lab02, sem conflitos. Seus pais são a main inicial e `489577a7`. O subtree
Lab03 permaneceu intacto nesse merge. Foram preservados os commits originais,
suas autorias e sua ancestralidade:

- `2761dcf9` — #33 [Lab02S03] Finalizar DOCX PDF e visualizações do relatório.
- `db12d630` — #33 [Lab02S03] Aplicar identidade visual ao relatório final.
- `262dc3ef` — Relatório + gráficos.
- `489577a7` — Create vinicius.md.

Os outros commits estruturais são `be3d925` (Lab01), `138bb03` (Lab02) e
`chore(repo): normalizar estrutura e documentação geral` (este relatório e
configuração global). Consulte `git log main..repo-consolidation` para os
identificadores completos, incluindo o último commit.

## Árvore anterior e proposta

```text
main inicial                         repo-consolidation
├── README.md do Lab02                ├── README.md índice geral
├── .gitignore                       ├── .gitignore
├── requirements.txt do Lab02         ├── pytest.ini
├── VALIDACAO.md do Lab02              ├── .github/consolidation/
├── src/api/ e src/katas/              ├── lab01/
├── snapshots/, data/, docs/          │   ├── README.md, requirements.txt
├── reports/ com conteúdo de labs     │   ├── Relatorio_Lab01.docx
├── lab02/ incompleto                 │   └── src/, tests/, data/, docs/, reports/, snapshots/
└── lab03/                            ├── lab02/
                                     │   ├── README.md, requirements.txt, VALIDACAO.md
                                     │   ├── src/katas/, trials/, metrics/, analysis/
                                     │   └── dashboard/, reporting/, reports/, simulations/
                                     └── lab03/ preservado
```

Inventários completos das fontes: [main](tree_main_source.txt),
[Lab01](tree_lab01_source.txt), [Lab02](tree_lab02_source.txt),
[Lab03](tree_lab03_source.txt) e [vinicius](tree_vinicius_source.txt).

## Matriz de preservação

| Laboratório | Arquivos fonte | Preservados | Movidos | Ajustados | Ausentes |
| --- | ---: | ---: | ---: | ---: | ---: |
| Lab01 | 80 | 80 | 80 | 1 | 0 |
| Lab02, incluindo .gitignore global | 158 | 158 | 37 | 17 | 0 |
| Lab03 | 23 | 23 | 0 | 1 | 0 |

Os 157 arquivos próprios do Lab02 estão em `lab02/`. O registro adicional é
`.gitignore`, que permaneceu global com as regras já presentes na main.
Dos 80 arquivos finais do Lab01, 58 estavam ausentes da main inicial, 3 tinham
versões diferentes e 19 já existiam como herança intacta. Os 80 foram
recuperados diretamente dos blobs finais do Lab01; somente seu README recebeu
instruções para execução na nova pasta. Os 37 caminhos do Lab02 fora de
`lab02/` foram realocados; seus outros 120 arquivos já tinham essa localização.

A [matriz por arquivo](preservation_manifest.csv) contém commit fonte,
caminhos anterior/final, blob Git original, SHA-256 canônicos, igualdade de
bytes no working tree, blob Git de destino e descrição de cada ajuste. Os
82 artefatos CSV/JSON/PNG/DOCX/PDF têm blobs Git idênticos aos originais; a
auditoria exige essa igualdade no índice, mesmo quando o checkout Windows
converte LF em CRLF. O [resumo CSV](preservation_summary.csv)
é gerado pela mesma auditoria. A normalização CRLF/LF só é usada na comparação
de texto entre plataformas; PNG, DOCX e PDF são comparados byte a byte.
Dados CSV/JSON e todos os artefatos científicos foram mantidos sem alteração
de conteúdo. Os ajustes estão limitados a caminhos, documentação e regras
globais; código, testes e dados do Lab03 são idênticos à fonte. Seu único
arquivo ajustado é o README.

Contagem de artefatos por extensão, considerando cada árvore classificada:

| Laboratório | DOCX | PDF | PNG | CSV | JSON | Markdown |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Lab01 | 2 | 0 | 17 | 11 | 2 | 10 |
| Lab02 | 1 | 1 | 13 | 23 | 8 | 19 |
| Lab03 | 0 | 0 | 0 | 2 | 2 | 3 |

As contagens de origem e destino coincidem; snapshots e soluções de trials
permanecem versionados. Nenhum artefato ausente foi inventado.

## O que faltava do Lab02

O merge adicionou 10 caminhos ausentes e atualizou 22 caminhos. A comparação
direta entre árvores finais também mostra README e .gitignore diferentes,
pois a main já continha ajustes posteriores do Lab03. A
[lista completa de diferenças](lab02_changes_missing_from_main.csv) distingue
os 10 ausentes dos 24 diferentes; não atribui automaticamente esses dois
arquivos globais a uma perda do Lab02.

Os 10 arquivos que não existiam na main eram:

- `lab02/reporting/__init__.py`.
- `lab02/reporting/build_final_report.py`.
- `lab02/reporting/build_template_report.py`.
- `lab02/reporting/qa_report.py`.
- `lab02/reporting/requirements.txt`.
- `reports/figures/rq1_mediana_participante.png`.
- `reports/figures/rq3_loc_complexidade_scatter.png`.
- `reports/final/lab02_relatorio_final.docx`.
- `reports/final/lab02_relatorio_final.pdf`.
- `reports/sprints/s03/vinicius.md`.

Os cinco últimos agora estão sob `lab02/reports/`.

Os 19 arquivos herdados e intactos do Lab01 foram classificados por comparação
de blobs e histórico Git. `src/api/`, `snapshots/` e os três relatórios
`reports/sprints/s01/{fernanda,islayder,vinicius}.md` são herança intacta, logo
existem somente em `lab01/`. Em particular, o s01 de Islayder tem o mesmo blob
nas duas fontes: não houve sobrescrita a preservar em duplicata. Relatórios
próprios do Lab02, incluindo `lab02_s01`, `lab02_s02` e `s03`, ficam no Lab02.

## Execução e verificações

Validação em Python 3.13.15, após instalar as dependências de cada laboratório
e as dependências de testes em seus requirements locais:

```powershell
# Lab01: imports src.* relativos ao diretório do laboratório.
Set-Location lab01
..\.venv\Scripts\python.exe -m pytest tests -q
Set-Location ..

# Lab02: somente os módulos reais de engenharia.
.\.venv\Scripts\python.exe -m pytest lab02/trials/tests lab02/metrics/tests lab02/analysis/tests lab02/dashboard/tests lab02/simulations/islayder_s02/tests -q

# Lab03 e suíte global.
.\.venv\Scripts\python.exe -m pytest lab03/tests -q
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m compileall -q lab01/src lab01/tests lab02 lab03 .github/consolidation

# Auditoria sem escrita; --write regenera os CSVs e inventários.
.\.venv\Scripts\python.exe .github/consolidation/audit.py
.\.venv\Scripts\python.exe .github/consolidation/audit.py --branches
```

Resultados: **Lab01 30 testes; Lab02 32; Lab03 71; global 133**, todos aprovados.
`compileall` também passou. O `pytest.ini` elimina as colisões de módulos
`test_solucao.py` selecionando somente suítes reais, sem modificar os arquivos
de snapshots, soluções experimentais ou stubs. Links Markdown locais foram
conferidos automaticamente. O smoke test do audit Lab03 processou 5 candidatos
e 5 ações pendentes, sem duplicatas.

O preparador/runner do Lab02 usa o novo `lab02/src/katas/`. A leitura de
`test_path` legado resolve `src/katas/` nesse diretório sem editar os CSVs
históricos. Defaults de gráficos, relatórios e QA apontam para `lab02/reports/`.
Os imports `src.*` do Lab01 continuam locais e o pytest global inclui `lab01`
no pythonpath. O README da raiz tem apenas instruções globais.

## Limitações preexistentes

- `build_final_report` exige 20 títulos, mas o Markdown final da fonte tem 5;
  gera o DOCX temporário e reprova sua própria validação. `qa_report` exige data
  e títulos de uma versão anterior do relatório. Ambas as falhas foram
  reproduzidas também com os scripts originais de `489577a7`, passando os
  arquivos finais como entradas. Os relatórios versionados foram preservados;
  a consolidação não modifica suas conclusões nem afrouxa os validadores.
- O PDF final preservado tem 12 páginas, todas com texto extraível; o QA de
  conteúdo acima continua pendente de alinhamento com o texto final.
- `build_template_report` exige `Template_Relatorio_Laboratorio.docx` externo,
  ausente do repositório e do Downloads deste ambiente. Nenhum template foi
  inventado. Os testes de geração/renderização usaram saídas em `.venv/`,
  ignoradas pelo Git.
- As limitações de token, datas ausentes e ações pendentes da coleta Lab03
  continuam registradas em seus relatórios, sem alteração nesta tarefa.
- Checkpoints e dados históricos podem conter caminhos do ambiente original;
  são evidência da execução original e permanecem intactos.

Mantenha as branches históricas durante a revisão. Após a validação e o merge,
a main será a fonte canônica, e as branches podem permanecer como histórico.
Use um merge que preserve os commits originais; squash/rebase eliminaria da
ancestralidade da main os quatro commits do Lab02 exigidos nesta consolidação.
