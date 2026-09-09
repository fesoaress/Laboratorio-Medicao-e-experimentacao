# Lab02 S01 — Islayder (Instrumentação e coleta dos trials)

## O que foi entregue

Foi desenvolvida a instrumentação responsável pela execução e coleta padronizada dos dados dos trials do experimento.

Artefatos implementados:

- `lab02/trials/config.py`: configurações gerais, caminhos e time-box de 35 minutos;
- `lab02/trials/test_runner.py`: execução automatizada dos testes dos katas com pytest;
- `lab02/trials/storage.py`: persistência dos dados coletados em CSV;
- `lab02/trials/run_trial.py`: controle do fluxo completo de cada trial;
- `lab02/trials/README.md`: documentação da instrumentação.

A instrumentação registra:

- participante;
- kata;
- tratamento (`IA` ou `Manual`);
- tempo de execução;
- testes passando e falhando;
- taxa de sucesso;
- número de ciclos de teste;
- status final (`green` ou `time-box`).

## Inovação

Além das métricas obrigatórias do experimento, foi adicionada a coleta da evolução da solução durante cada trial.

A cada execução dos testes são registrados:

- tempo decorrido;
- quantidade de testes passando e falhando;
- taxa de sucesso;
- número do ciclo.

Esses dados permitirão analisar posteriormente a velocidade de progresso e a quantidade de ciclos/retrabalho necessários até atingir o estado `green`, comparando os tratamentos com IA e sem IA.

## Decisões metodológicas

- Time-box máximo de 35 minutos por trial.
- Trials que atingirem o limite serão registrados como `time-box`, sem descarte.
- O tempo será medido desde o início do trial até o estado `green` ou até o limite.
- Os testes automatizados dos katas serão executados pela própria instrumentação.
- O resultado final será armazenado em `trials.csv`.
- A evolução intermediária será armazenada em `trial_cycles.csv`.
- Os dois tratamentos utilizarão a mesma estrutura de coleta, evitando diferenças no processo de medição.

## Como utilizar

A instrumentação é iniciada por:

```bash
python lab02/trials/run_trial.py