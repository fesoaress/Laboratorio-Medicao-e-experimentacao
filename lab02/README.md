# Lab02 — Katas e Testes Automatizados (Vinicius)

Linguagem: **Python 3.11+**
Dependência dos trials: `pytest` (versão fixada em [trials/requirements.txt](trials/requirements.txt))

## Estrutura

```
lab02/src/katas/
├── kata1_normalizador_etiquetas/
│   ├── solucao.py        <- arquivo que o participante edita durante o trial
│   └── test_solucao.py   <- testes de aceitação (não editar)
├── kata2_balanceamento_turnos/
├── kata3_compactador_sensor/
├── kata4_manutencao_preditiva/
└── gabarito/              <- uso interno do grupo, NÃO entregar ao participante
```

## Como rodar um trial

Use obrigatoriamente o preparador e o runner documentados em [trials/README.md](trials/README.md). O preparador copia somente o stub e os testes para um workspace isolado; o runner registra cada ciclo, impõe o time-box e arquiva o código final sem alterar `lab02/src/katas` nem `gabarito/`.

## Por que esses 4 katas

Critério pedido pelo professor: **dificuldade comparável** e **baixa indexação** (evitar exercícios clássicos tipo LeetCode/HackerRank que a IA pode ter "decorado").

| Kata | Domínio | Padrão algorítmico de base | Por que baixa indexação |
|---|---|---|---|
| 1 — Normalizador de Etiquetas | Estoque/manufatura | Parsing + validação de formato | Regras de normalização são específicas nossas (formato "AA-9999", tratamento de espaços/hífens), não é um exercício nomeado conhecido |
| 2 — Balanceamento de Turnos | RH/operações | Redistribuição em array com restrição de capacidade | Formulação de "nº mínimo de transferências" com capacidade máxima é uma variação própria, não o enunciado padrão de nenhum kata famoso |
| 3 — Compactador de Leituras de Sensor | IoT/monitoramento | Run-length encoding com limiar mínimo | RLE clássico existe, mas a regra do limiar (só comprime run ≥ N) e a saída em tuplas mistas é uma variação autoral |
| 4 — Manutenção Preditiva | Manutenção industrial | Média móvel sobre janela | Média móvel é conhecida, mas a regra de janela parcial no início + retorno de índices de alerta é específica do enunciado |

Todos os 4 usam **funções puras, um único arquivo de solução e nenhuma biblioteca externa**, o que reduz diferenças de setup. Isso não prova equivalência de dificuldade: a auditoria em `VALIDACAO.md` encontrou variação estrutural e exige piloto temporal com não participantes antes da S02.

## Validação de equivalência

Ver `VALIDACAO.md` — cada kata foi resolvido com o gabarito de referência e todos os testes passam (script rodado e evidenciado).

## Ameaças à validade (apoio a este bloco no desenho do experimento)

- **Efeito de aprendizado entre katas**: como o mesmo participante resolve os 4 (2 com IA, 2 sem, ordem contrabalanceada), a ordem de apresentação foi desenhada para ser diferente entre os 3 integrantes — evita que "o último kata sempre fica mais rápido só por prática".
- **Vazamento de solução já vista**: nenhum dos 4 katas é uma cópia literal de exercício público amplamente indexado; são variações autorais sobre padrões conhecidos (parsing, RLE, média móvel, alocação em array), então mesmo que a IA reconheça o *padrão* geral, ela não pode colar uma solução pronta de memória — precisa adaptar às regras específicas de cada enunciado.
- **Memorização pela IA**: caso o grupo perceba, ao testar, que a IA acerta de primeira sem iteração em algum kata, isso deve ser registrado como observação qualitativa (nº de prompts) e discutido no relatório como limitação.
- **Dificuldade desigual entre katas**: permanece como risco; deve ser mitigada por piloto temporal, contrabalanceamento de cada kata entre tratamentos e controle do identificador do kata na análise — ver `VALIDACAO.md`.

## Execução após a consolidação

Execute os comandos abaixo na raiz do repositório. O Lab02 preserva seus
resultados e snapshots de trials; o Lab01 possui código e dados separados.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r lab02/requirements.txt -r lab02/trials/requirements.txt -r lab02/metrics/requirements.txt
.\.venv\Scripts\python.exe -m pytest lab02/trials/tests lab02/metrics/tests lab02/analysis/tests lab02/dashboard/tests lab02/simulations/islayder_s02/tests -q
```

Katas e gabaritos ficam em `lab02/src/katas/`. O preparador e o runner continuam
usando `python -m lab02.trials.prepare_trial` e `python -m lab02.trials.run_trial`.
CSV histórico que menciona `src/katas/` permanece intacto; o leitor resolve
essa referência para `lab02/src/katas/`.

Relatórios, gráficos e sprints ficam em `lab02/reports/`:

- [Relatório final Markdown](reports/final/lab02_relatorio_final.md)
- [Relatório final DOCX](reports/final/lab02_relatorio_final.docx)
- [Relatório final PDF](reports/final/lab02_relatorio_final.pdf)
- [Análises e critérios](analysis/README.md)
- [Instrumentação de trials](trials/README.md)
- [Métricas estruturais](metrics/README.md)

`reporting/requirements.txt` contém dependências opcionais de geração e
inspeção dos relatórios. Os arquivos finais foram preservados da branch
`Laboratorio-2` em `489577a7`, sem regerar DOCX, PDF ou gráficos versionados.
O gerador `build_final_report` e o validador `qa_report` têm expectativas de
uma versão anterior do texto; suas falhas históricas estão documentadas na
[auditoria global](../.github/consolidation/README.md). O gerador com template
exige um arquivo DOCX externo que não está versionado no repositório.
