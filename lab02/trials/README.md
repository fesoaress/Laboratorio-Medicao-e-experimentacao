# Instrumentação dos trials — Lab02

Este módulo prepara e executa trials isolados, limita cada execução a 35 minutos e registra tanto o resultado final quanto cada ciclo de testes. Execute os comandos a partir da raiz do repositório com Python 3.11+.

## Preparação do ambiente

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lab02\trials\requirements.txt
```

No Linux/macOS, substitua `.\.venv\Scripts\python.exe` por `.venv/bin/python`.

## Alocação na S02

### Islayder e Vinicius

| Ordem | Kata | Tratamento |
|---:|---|---|
| 1 | `kata1_normalizador_etiquetas` | IA |
| 2 | `kata2_balanceamento_turnos` | Manual |
| 3 | `kata3_compactador_sensor` | IA |
| 4 | `kata4_manutencao_preditiva` | Manual |

O preparador rejeita uma combinação diferente para Islayder.

### Fernanda (tratamento oposto + ordem contrabalanceada)

| Ordem | Kata | Tratamento |
|---:|---|---|
| 1 | `kata2_balanceamento_turnos` | IA |
| 2 | `kata1_normalizador_etiquetas` | Manual |
| 3 | `kata4_manutencao_preditiva` | IA |
| 4 | `kata3_compactador_sensor` | Manual |

O preparador rejeita uma combinação diferente para Fernanda. Roteiro completo: `lab02/trials/FERNANDA_S02.md`.

## Procedimento obrigatório para cada trial

Antes do primeiro trial real, confirme que o grupo concluiu o piloto temporal com pessoas fora da amostra e definiu a matriz contrabalanceada dos três integrantes. O piloto não deve usar Islayder, Fernanda ou Vinicius nem entrar nos CSVs oficiais.

1. Antes da execução, confirme no GitHub que a Issue individual existe, está atribuída ao participante e corresponde ao kata e tratamento definidos na matriz. Anote seu número. O preparador normalmente impede reutilizar uma Issue presente em um workspace ou em `trials.csv`, mas permite a reexecução oficial de Fernanda nas Issues `#19`, `#27`, `#29` e `#28` somente quando a ocorrência anterior é o ensaio inválido documentado. Não inicie dois trials ao mesmo tempo.
2. Confirme o tratamento. Nos trials `IA`, use sempre o mesmo assistente e versão. Nos trials `Manual`, desabilite assistentes e não consulte chatbots ou soluções externas.
3. Prepare uma cópia isolada, trocando `<ISSUE>` pelo número real:

   ```powershell
   .\.venv\Scripts\python.exe -m lab02.trials.prepare_trial `
     --participant Islayder `
     --kata kata1_normalizador_etiquetas `
     --treatment IA `
     --issue <ISSUE>
   ```

4. Abra no editor **somente** a pasta exibida pelo comando. Ela contém apenas `solucao.py`, `test_solucao.py` e `trial.json`; o gabarito não é copiado. **Não edite a solução nem consulte a IA antes de iniciar o cronômetro.**
5. Inicie o cronômetro instrumentado apontando para a pasta exibida:

   ```powershell
   .\.venv\Scripts\python.exe -m lab02.trials.run_trial `
     --workspace lab02\trials\workspaces\islayder\<PASTA_EXIBIDA>
   ```

6. Depois que o cronômetro começar, edite somente `solucao.py` e, nos trials IA, inicie a interação com o assistente. Pressione ENTER sempre que quiser executar os testes. Cada execução vira um ciclo em `trial_cycles.csv`.
7. Pare de editar quando aparecer `green` ou `time-box`. No time-box, o script encerra o período aos 35 minutos, executa uma leitura final dos testes e registra o tempo censurado como 2.100 segundos.
8. Consulte em `trials.csv` o campo `codigo_path`. Ele aponta para o snapshot final que deve ser usado nas métricas estruturais e referenciado no relatório S02.
9. Colete RQ3 sobre esse snapshot, sem analisar testes:

   ```powershell
   .\.venv\Scripts\python.exe lab02\metrics\run_metrics.py <codigo_path> `
     --participant Islayder `
     --kata kata1_normalizador_etiquetas `
     --treatment IA `
     --trial-id <trial_id_de_trials.csv> `
     --issue <ISSUE>
   ```

10. Preencha `reports/sprints/lab02_s02/islayder.md` e depois faça manualmente o commit referenciando a Issue.

Repita o procedimento para os quatro katas, alterando `--kata`, `--treatment` e `--issue` conforme a tabela. O workspace nunca é sobrescrito nem reutilizado. A reexecução oficial de Fernanda reaproveita as quatro Issues antigas, mas cria novos workspaces e novos `trial_id`; outras repetições continuam exigindo decisão explícita do grupo.

## Saídas

- `lab02/trials/results/trials.csv`: uma linha por trial, com Issue, tempo, estado final, testes, taxa de sucesso, ciclos e caminho do código.
- `lab02/trials/results/trial_cycles.csv`: uma linha por execução de testes, incluindo falhas de coleta do pytest.
- `lab02/trials/results/solutions/<trial_id>/`: snapshot final de `solucao.py` e dos testes de aceitação.
- `lab02/trials/workspaces/`: área transitória ignorada pelo Git; os katas originais e o gabarito nunca são modificados pelo runner.

Os CSVs são escritos de forma atômica e usam `trial_id` para evitar duplicatas. Erros de importação, sintaxe ou coleta contam os testes não executados como não passantes, sem produzir falso `green`.

Os coletores de execuções reais gravam `source_kind=observed`. Cenários simulados autorizados para ensaio metodológico usam `source_kind=observed_simulated`, ID `SIM-*` e status `simulated-*`. Esses registros não têm snapshot nem tempo observado e devem ser identificados separadamente de qualquer resultado experimental humano.

Os trials IA #21 e #25 de Islayder foram executados com Gemini no celular,
cronometrados fora do runner e informados pelo participante. Para preservar a
distinção metodológica sem fabricar timestamps, snapshots ou IDs instrumentados,
eles ficam em `results/participant_reported_trials.csv` com
`source_kind=participant_reported_observed`. A análise gera um único ciclo final
a partir do campo `ciclos=1`, exatamente como informado, e valida o total de
testes diretamente nos respectivos `test_solucao.py`.

## Interrupções

`Ctrl+C` gera o status `interrupted`, salva o snapshot possível e persiste uma linha final coerente. Esse registro não deve ser tratado como trial válido na análise; registre a ocorrência e repita apenas com uma nova Issue, conforme decisão do grupo.

## Compatibilidade e testes da instrumentação

Os módulos usam o mesmo interpretador Python que iniciou o runner (`sys.executable`) e caminhos via `pathlib`, funcionando em Windows e Linux. Valide sem gerar dados oficiais:

```powershell
.\.venv\Scripts\python.exe -m pytest -q lab02\trials\tests
```
