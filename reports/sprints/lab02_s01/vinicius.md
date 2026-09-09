# Lab02 S01 — Vinicius (Katas e testes automatizados)

## O que foi entregue

Foram desenvolvidos os katas do experimento e os respectivos testes automatizados de aceitação, que servirão de base para a execução dos trials (S02) e para a instrumentação de coleta do Islayder.

Artefatos implementados:

- `lab02/katas/kata1_normalizador_etiquetas/solucao.py` + `test_solucao.py`;
- `lab02/katas/kata2_balanceamento_turnos/solucao.py` + `test_solucao.py`;
- `lab02/katas/kata3_compactador_sensor/solucao.py` + `test_solucao.py`;
- `lab02/katas/kata4_manutencao_preditiva/solucao.py` + `test_solucao.py`;
- `lab02/katas/gabarito/` (soluções de referência, uso interno do grupo, não distribuído aos participantes);
- `lab02/katas/README.md`: documentação dos katas e do fluxo de execução de um trial;
- `lab02/katas/VALIDACAO.md`: evidência da validação de equivalência entre os katas.

Cada kata é uma função pura em Python, sem dependências externas, resolvível em até 35 minutos:

- **Kata 1** — Normalizador de Etiquetas de Estoque (parsing e validação de formato);
- **Kata 2** — Balanceamento de Turnos (redistribuição em array com restrição de capacidade);
- **Kata 3** — Compactador de Leituras de Sensor (run-length encoding com limiar mínimo);
- **Kata 4** — Manutenção Preditiva (média móvel com janela parcial).

## Critérios de seleção

- Dificuldade comparável entre os 4 katas: função única, sem I/O, sem bibliotecas externas, solução de referência entre 6 e 12 linhas.
- Baixa indexação: nenhum é cópia literal de exercício público amplamente conhecido (LeetCode/HackerRank); todos usam regras de negócio autorais sobre padrões algorítmicos comuns, reduzindo o risco de a IA reproduzir uma solução já vista no treinamento em vez de efetivamente resolver o problema.
- Número par (4), permitindo divisão exata entre trials com e sem IA por participante.

## Validação de equivalência

Cada kata foi resolvido com uma solução de referência e testado contra seus testes de aceitação:

| Kata | Nº de testes | Stub vazio (antes) | Gabarito (depois) |
|---|---|---|---|
| 1 — Normalizador de Etiquetas | 10 | 0/10 | 10/10 |
| 2 — Balanceamento de Turnos | 9 | 0/9 | 9/9 |
| 3 — Compactador de Sensor | 9 | 0/9 | 9/9 |
| 4 — Manutenção Preditiva | 7 | 0/7 | 7/7 |

O stub original (entregue ao participante) começa em 0% de testes passando em todos os katas — importante para a métrica de inovação do grupo, já que todo trial parte do mesmo ponto zero na curva de evolução coletada pela instrumentação do Islayder.

## Apoio às ameaças à validade

- **Efeito de aprendizado entre katas**: mitigado pela ordem contrabalanceada entre os 3 integrantes, já que todos resolvem os mesmos 4 katas.
- **Vazamento de solução já vista / memorização pela IA**: reduzido pelo uso de enunciados autorais, mesmo quando o padrão algorítmico de base é conhecido (parsing, RLE, média móvel, alocação em array).
- **Dificuldade desigual entre katas**: mitigada pela padronização estrutural (função pura, sem libs externas, 7 a 10 casos de teste por kata cobrindo caso feliz, caso vazio e casos de borda).

## Decisões metodológicas

- Cada kata roda isoladamente (`pytest test_solucao.py` dentro da própria pasta), evitando conflito de nome entre os arquivos `test_solucao.py` de katas diferentes.
- Apenas `solucao.py` (resetado ao stub original) e `test_solucao.py` devem ser copiados para o ambiente de cada trial na S02.
- A pasta `gabarito/` não deve estar acessível ao participante durante o trial, para não vazar a solução.
- Linguagem fixada em Python 3.11+, sem dependências além de `pytest` — compatível com o Radon que a Fernanda usará no RQ3.

## Como utilizar

Rodar os testes de um kata:

```bash
cd lab02/katas/kata1_normalizador_etiquetas
pytest test_solucao.py -v
```
