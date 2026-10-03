# Validação dos Katas — S01

Ambiente: Python 3.12.3, pytest 9.1.1, sem dependências externas além do stdlib.

## Resultado da validação

Cada kata foi resolvido com uma solução de referência (pasta `gabarito/`, uso
interno, não distribuir aos participantes) e testado contra `test_solucao.py`.

| Kata | Nº de testes | Stub vazio (antes) | Gabarito (depois) |
|---|---|---|---|
| 1 — Normalizador de Etiquetas | 10 | 0/10 (NotImplementedError) | 10/10 ✅ |
| 2 — Balanceamento de Turnos | 9 | 0/9 (NotImplementedError) | 9/9 ✅ |
| 3 — Compactador de Sensor | 9 | 0/9 (NotImplementedError) | 9/9 ✅ |
| 4 — Manutenção Preditiva | 7 | 0/7 (NotImplementedError) | 7/7 ✅ |

Isso confirma:
- Os 4 katas têm solução válida e os testes de aceitação estão corretos
  (nenhum teste com bug/ambiguidade que impeça 100% de sucesso).
- O estado inicial (`solucao.py` como entregue ao participante) começa em
  0% de testes passando, o que é importante para a métrica de inovação do
  grupo (evolução do % de testes passando ao longo do trial e nº de ciclos
  até o green) — todo trial parte do mesmo ponto zero.
- Cada kata roda isoladamente com `pytest test_solucao.py`, sem
  dependências entre pastas (evita o erro de "import file mismatch" do
  pytest quando dois `test_solucao.py` de pastas diferentes são coletados
  juntos — rodar sempre kata por kata, não a raiz inteira).

## Comparabilidade de dificuldade (avaliação qualitativa e estrutural)

Todos os 4 katas compartilham as mesmas características estruturais:
- Função pura, single-file, sem I/O e sem bibliotecas externas.
- 1 a 2 conceitos centrais por kata (parsing+regex / soma condicional /
  agrupamento de sequência / janela deslizante), sem combinar múltiplos
  algoritmos no mesmo kata.
- 7 a 10 casos de teste cobrindo: caso feliz, caso vazio, e pelo menos
  2 casos de borda específicos da regra de negócio de cada kata.

Nenhum dos katas exige estrutura de dados além de listas/tuplas nativas do
Python, o que reduz variância de dificuldade ligada a familiaridade com
bibliotecas.

Uma auditoria estrutural posterior, executada com Radon 6.0.1 sobre cópias
temporárias dos gabaritos, encontrou:

| Kata | LOC lógico | Funções | CC média | CC máxima |
|---|---:|---:|---:|---:|
| 1 — Normalizador de Etiquetas | 14 | 1 | 6,0 | 6 |
| 2 — Balanceamento de Turnos | 4 | 1 | 4,0 | 4 |
| 3 — Compactador de Sensor | 15 | 2 | 3,0 | 4 |
| 4 — Manutenção Preditiva | 10 | 1 | 3,0 | 3 |

Portanto, os katas têm escopo funcional semelhante, mas a equivalência de
dificuldade **não está demonstrada** apenas por LOC/CC; o Kata 2 é
estruturalmente menor e o Kata 1 concentra mais decisões. Antes dos trials
reais, o grupo deve fazer um piloto de tempo com pessoas que não participarão
da amostra. Além disso, a alocação dos três integrantes deve contrabalançar
cada kata entre IA e Manual. Na análise, mantenha o identificador do kata e
discuta-o como possível fator de confusão, sem agregar tratamentos de forma
ingênua.

## Observação para a S02

Ao copiar a pasta de um kata para um trial, copiar **apenas** `solucao.py`
(resetado para o stub original) + `test_solucao.py`. A pasta `gabarito/`
não deve estar acessível ao participante durante o trial, para não vazar a
solução.

Use `python -m lab02.trials.prepare_trial` para fazer essa cópia; o comando
exclui o gabarito e recusa sobrescrever um workspace existente.
