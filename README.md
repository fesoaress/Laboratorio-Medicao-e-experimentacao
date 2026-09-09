# Lab02 — Katas e Testes Automatizados (Vinicius)

Linguagem: **Python 3.11+**
Dependência única: `pytest` (`pip install pytest`)

## Estrutura

```
lab02-katas/
├── kata1_normalizador_etiquetas/
│   ├── solucao.py        <- arquivo que o participante edita durante o trial
│   └── test_solucao.py   <- testes de aceitação (não editar)
├── kata2_balanceamento_turnos/
├── kata3_compactador_sensor/
├── kata4_manutencao_preditiva/
└── gabarito/              <- uso interno do grupo, NÃO entregar ao participante
```

## Como rodar um trial

1. Copiar a pasta do kata (ex: `kata1_normalizador_etiquetas/`) para o ambiente do trial.
2. Cronômetro do Islayder começa.
3. Participante edita **apenas** `solucao.py` (com ou sem IA, conforme tratamento sorteado).
4. Rodar os testes quantas vezes quiser durante o trial:
   ```
   pytest kata1_normalizador_etiquetas/test_solucao.py -v
   ```
5. Trial encerra em sucesso (todos os testes verdes) ou ao atingir 35 min (time-box).
6. Script de coleta do Islayder registra, a cada rodada de teste, quantos passaram — é isso que dá o "número de ciclos até o green" da nossa inovação.

## Por que esses 4 katas

Critério pedido pelo professor: **dificuldade comparável** e **baixa indexação** (evitar exercícios clássicos tipo LeetCode/HackerRank que a IA pode ter "decorado").

| Kata | Domínio | Padrão algorítmico de base | Por que baixa indexação |
|---|---|---|---|
| 1 — Normalizador de Etiquetas | Estoque/manufatura | Parsing + validação de formato | Regras de normalização são específicas nossas (formato "AA-9999", tratamento de espaços/hífens), não é um exercício nomeado conhecido |
| 2 — Balanceamento de Turnos | RH/operações | Redistribuição em array com restrição de capacidade | Formulação de "nº mínimo de transferências" com capacidade máxima é uma variação própria, não o enunciado padrão de nenhum kata famoso |
| 3 — Compactador de Leituras de Sensor | IoT/monitoramento | Run-length encoding com limiar mínimo | RLE clássico existe, mas a regra do limiar (só comprime run ≥ N) e a saída em tuplas mistas é uma variação autoral |
| 4 — Manutenção Preditiva | Manutenção industrial | Média móvel sobre janela | Média móvel é conhecida, mas a regra de janela parcial no início + retorno de índices de alerta é específica do enunciado |

Todos os 4 são **funções puras, single-file, sem libs externas**, resolvíveis por alguém com Python intermediário em até ~35 min — isso equaliza a dificuldade entre eles (nenhum depende de bibliotecas externas ou setup de ambiente diferente).

## Validação de equivalência

Ver `VALIDACAO.md` — cada kata foi resolvido com o gabarito de referência e todos os testes passam (script rodado e evidenciado).

## Ameaças à validade (apoio a este bloco no desenho do experimento)

- **Efeito de aprendizado entre katas**: como o mesmo participante resolve os 4 (2 com IA, 2 sem, ordem contrabalanceada), a ordem de apresentação foi desenhada para ser diferente entre os 3 integrantes — evita que "o último kata sempre fica mais rápido só por prática".
- **Vazamento de solução já vista**: nenhum dos 4 katas é uma cópia literal de exercício público amplamente indexado; são variações autorais sobre padrões conhecidos (parsing, RLE, média móvel, alocação em array), então mesmo que a IA reconheça o *padrão* geral, ela não pode colar uma solução pronta de memória — precisa adaptar às regras específicas de cada enunciado.
- **Memorização pela IA**: caso o grupo perceba, ao testar, que a IA acerta de primeira sem iteração em algum kata, isso deve ser registrado como observação qualitativa (nº de prompts) e discutido no relatório como limitação.
- **Dificuldade desigual entre katas**: mitigada por todos serem funções isoladas de complexidade comparável (sem dependências externas, ~20-35 linhas de solução de referência cada) — ver `VALIDACAO.md` para os tempos de referência.
