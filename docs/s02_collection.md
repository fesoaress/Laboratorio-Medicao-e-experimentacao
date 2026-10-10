# Coleta real Lab03 S02

Branch: `Laboratorio-3`. Janela UTC `[2025-10-01, 2026-10-01)`, fim exclusivo,
definida pelo grupo em 10/10/2026 porque as datas não constavam do material.
`config/s01.json` registra essas datas; não são apresentadas como datas do enunciado.

## Execução local e retomada

O programa usa `GITHUB_TOKEN` do ambiente. Se estiver somente no `.env`, carregue-o
apenas no processo local. O `.env` é ignorado pelo Git; nunca copie seu conteúdo
para configuração, manifesto, código ou linha de comando. Exemplo PowerShell:

```powershell
# Opcional: somente para o carregamento local de .env.
.\.venv\Scripts\python.exe -m pip install python-dotenv==1.2.4
@'
from dotenv import load_dotenv
load_dotenv('.env', override=True)
import os
print('GITHUB_TOKEN disponível: ' + ('sim' if os.environ.get('GITHUB_TOKEN', '').strip() else 'não'))
from src.s02_collection import main
raise SystemExit(main(['--workers', '8']))
'@ | .\.venv\Scripts\python.exe -u -
```

Repetir o mesmo comando retoma os checkpoints de `data/raw/s02/checkpoints/`.
`selected` e `discarded` não são coletados novamente. Erros explícitos podem ser
retentados. Uma janela diferente é recusada. `--target` deve ser pelo menos 300;
o alvo conta **elegíveis**, sem limitar a busca a 300 candidatos. Tarefas já
submetidas são concluídas ao atingir o alvo, portanto o total pode exceder 300.
Somente inicie o sorteio quando `collection_manifest_s02.json` confirmar
`target_met=true` e `final_sample>=300`.

Antes do sorteio, confira os dados efetivamente exportados, incluindo contagens
de releases/runs, IDs únicos, janela exclusiva, público/Actions e snapshot:

```powershell
.\.venv\Scripts\python.exe -m src.s02_audit data/processed/s02
```

O comando grava `collection_audit_s02.json` com hashes das fontes e retorna erro
se houver contradições ou menos de 300 elegíveis. Para inspecionar uma coleta
parcial, use `--allow-partial`; `ready_for_gold_sample` continua `false`.

## Critérios e estratégia

Critérios preservados da S01: público, `stars>1000`, Actions, default branch
identificada e resolvida, pelo menos 5 releases publicadas não draft/não
prerelease dentro da janela e ancestrais do SHA registrado da default branch,
pelo menos 50 runs válidos `push` nessa branch dentro da janela. Sucesso e
falha (incluindo `timed_out`/`startup_failure`) contam; conclusões ignoradas
permanecem nos dados e não contam para a elegibilidade.

A busca subdivide faixas de estrelas até cada consulta ter no máximo 1.000
resultados e segue todas as páginas necessárias. Prioriza as faixas
5001–10000, 10001–20000, 20001–50000, 50001+, 2001–5000 e 1001–2000,
ordenando por estrelas dentro de cada folha. Execuções iniciais também usaram
1001–2000; seus checkpoints são preservados. O prefilter `pushed>=2025-10-01`
é necessário para haver pushes na janela. A ordem introduz viés de popularidade
e de disponibilidade de dados; esta amostra não representa uniformemente todo o GitHub.

GraphQL preserva metadados e todas as páginas de releases com notes/body.
Um pré-filtro reprova contagens publicadas estáveis abaixo de 5 **antes** das
chamadas REST de Actions/contribuidores. Portanto, Actions/contribuidores desses
descartes podem estar não medidos. Isso não equivale a ausência de Actions.
Após o pré-filtro, os componentes S01 de metadados são reutilizados.
Ancestralidade é verificada antes dos runs para evitar consultas REST em
repositórios que já falham nas releases. Checkpoints iniciais usaram a ordem
inversa; os testes pulados por uma reprovação anterior ficam não medidos no funil.
Runs são coletados com paginação e subdivisão temporal quando a consulta anuncia
mais de 1.000 itens. O total de IDs únicos precisa corresponder ao anunciado.

As tags reais das releases são resolvidas por `Release.tagCommit`. A comparação
`Ref.compare(headRef=SHA_snapshot)` verifica os OIDs de base e head, aprovando
apenas `AHEAD`/`IDENTICAL`. Se faltam evidências, o coletor usa REST ou registra
erro; nunca infere ancestralidade de `target_commitish` nem do nome da branch.
O primeiro SHA observado é mantido como snapshot, mesmo se novos pushes ocorrerem
durante a paginação. A elegibilidade consulta todas as releases na janela em
lotes GraphQL, inclusive prereleases, evitando resolução REST redundante.
Releases anteriores à janela só são verificadas no enriquecimento dos elegíveis,
até encontrar a predecessora estável ancestral mais recente, necessária aos intervalos.

Cache e checkpoints são locais e ignorados pelo Git. O cliente REST espera o
reset de quota e usa backoff em 5xx; GraphQL também repete falhas transitórias
e espera o reset quando a quota é sinalizada no corpo de uma resposta HTTP 200.
Respostas GraphQL e REST são preservadas sem headers de autenticação.
Prefetch local apenas adianta o cache e não constitui amostra nem limite final
de candidatos. Um erro nunca é convertido em zero ou aprovação.

Completude da paginação significa correspondência com o total anunciado pela
API durante a consulta. Não garante recuperar objetos anteriormente apagados.
A documentação do GitHub descreve políticas de retenção para workflow runs,
incluindo uma mudança de aplicação dessas políticas em 01/10/2026. Assim,
as contagens e métricas descrevem os registros disponíveis e coletados dentro
da janela; não se deve inferir ausência histórica de atividade quando faltam
registros. A aprovação comprova pelo menos 50 runs válidos observados. Não
atribuímos os erros de paginação de um projeto específico à retenção sem prova.
Fonte: [retenção de workflow runs no GitHub](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/enabling-features-for-your-repository/managing-github-actions-settings-for-a-repository#configuring-the-retention-period-for-checks-workflow-runs-commit-statuses-artifacts-and-logs-in-your-repository).

## Contexto e métricas

Depois da seleção, execute, com o mesmo carregamento local do `.env`:

```python
from src.s02_enrichment import main
raise SystemExit(main(['--workers', '4']))
```

O enriquecimento reutiliza `collect_release_intervals`, `calculate_lead_time`,
`change_failure_rate_a`, `recovery_episodes` e `repository_recovery_time`.
Tags são paginadas e desreferenciadas, inclusive anotadas. O CSV contém tags
cujo `commit.authoredDate` está na janela; todas as refs examinadas ficam no
cache bruto. Sua ancestralidade usa o mesmo snapshot da seleção.

Comparações GraphQL entre releases são paginadas e conferidas contra
`totalCount`. Em testes reais, algumas conexões terminaram em 1.000 itens mesmo
anunciando mais; nesses casos o coletor usa a comparação REST completa por SHA.
Tags movidas/removidas também exigem REST pelo SHA preservado. Nenhuma lista
truncada é aceita como completa. Intervalos divergentes, erros e Lead Time
negativo ficam explícitos, com métricas ausentes e dados brutos preservados.
Erros de métricas não inventam uma nova regra de exclusão da elegibilidade.

## Artefatos

Em `data/processed/s02/`:

- `repositories_s01.csv`: todos os candidatos com tentativa concluída e motivos.
- `repositories_final_s02.csv`: elegíveis comprovados; durante a coleta é
  provisório e deve ser lido junto de `target_met` no manifesto.
- `selection_funnel_s02.csv`: etapas comprovadas, descartes e não medidos.
  A avaliação antecipada de releases pode deixar Actions não medido em descartes.
- `collection_manifest_s02.json`: janela/origem, consultas, estratégia, contagens,
  alvo e interrupções; contagens anunciadas de buscas sobrepostas não são somadas.
- `releases_s01.csv`: releases ancestrais, publicação, SHA, nome e notes/body,
  com flags de inclusão. Checkpoints iniciais também incluem a predecessora externa;
  `release_predecessors_s02.csv` conserva todas as predecessoras usadas no enriquecimento.
- `workflow_runs_s02.csv`: runs factuais, inclusive conclusões ignoradas.
- `tags_s01.csv`, `release_intervals_s01.csv`, `release_commits_s01.csv`:
  contexto verificável para métricas e validação humana.
- `lead_time*_s01.csv`, `workflow_metrics_s02.csv`, `recovery_episodes_s02.csv`:
  métricas e episódios com censura preservada.
- `enrichment_manifest_s02.json`: escopo das tags, status por repositório e erros.

Nenhuma heurística corretiva, classificação humana ou Kappa é executada por
esses coletores. O smoke continua separado em `data/processed/smoke/`.

Os CSVs completos de releases, runs e commits ficam disponíveis localmente,
mas podem ultrapassar o limite de tamanho de um blob no GitHub. Versione seus
snapshots `.csv.gz`; os três `.csv` correspondentes são ignorados pelo Git.
Depois de concluir a coleta e o enriquecimento, recrie os gzip e confira a igualdade
byte a byte por SHA-256, sem selecionar ou cortar commits:

```python
import gzip
import hashlib
import shutil
from pathlib import Path

for name in ('releases_s01.csv', 'workflow_runs_s02.csv', 'release_commits_s01.csv'):
    source = Path('data/processed/s02') / name
    target = source.with_suffix('.csv.gz')
    with source.open('rb') as incoming, target.open('wb') as outgoing:
        with gzip.GzipFile(filename='', fileobj=outgoing, mode='wb', mtime=0) as compressed:
            shutil.copyfileobj(incoming, compressed)
    with source.open('rb') as original, gzip.open(target, 'rb') as restored:
        if hashlib.file_digest(original, 'sha256').digest() != hashlib.file_digest(restored, 'sha256').digest():
            raise RuntimeError('Snapshot comprimido difere do CSV original.')
```

O gzip usa timestamp fixo e não inclui nome local no cabeçalho, permitindo
reproduzir o mesmo snapshot. Não compacte enquanto o enriquecimento estiver
reescrevendo o CSV. Para recuperar o arquivo após um clone, use `gzip.open`
e `shutil.copyfileobj` no sentido inverso.
A auditoria prefere os snapshots comprimidos e recusa um gzip desatualizado
se o CSV local também existe. Ela também funciona depois de um clone, quando
somente os gzip versionados estão presentes. `.gitattributes` evita conversão
de fim de linha nos artefatos, preservando os bytes usados nos hashes.

## Testes

```powershell
.\.venv\Scripts\python.exe -m pytest -q --cov=src --cov-report=term-missing
```

Fixtures dos testes são identificadas como sintéticas e não entram na coleta real.

Referências primárias: [workflow runs REST](https://docs.github.com/en/rest/actions/workflow-runs#list-workflow-runs-for-a-repository),
[refs GraphQL](https://docs.github.com/en/graphql/reference/git#ref),
[comparações GraphQL](https://docs.github.com/en/graphql/reference/commits#comparison),
[releases GraphQL](https://docs.github.com/en/graphql/reference/releases).
