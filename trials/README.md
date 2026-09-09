# Instrumentação dos Trials — Lab02

Este módulo é responsável pela instrumentação e coleta de dados dos trials do experimento do Laboratório 02.

O objetivo é registrar de forma padronizada os dados necessários para comparar a resolução de katas com e sem assistência de IA.

## Estrutura

- `config.py`: define caminhos e configurações gerais do experimento.
- `test_runner.py`: executa os testes automatizados dos katas e extrai os resultados.
- `storage.py`: grava os resultados dos trials e dos ciclos de teste em arquivos CSV.
- `run_trial.py`: controla a execução completa de um trial.
- `results/`: diretório onde os dados coletados serão armazenados.

## Dados coletados por trial

Para cada trial são registrados:

- participante;
- kata;
- tratamento (`IA` ou `Manual`);
- tempo total de resolução;
- quantidade de testes passando;
- quantidade de testes falhando;
- total de testes;
- taxa de sucesso;
- número de ciclos de execução dos testes;
- status final (`green` ou `time-box`).

O limite máximo de execução é de 35 minutos por trial.

## Inovação do experimento

Além das métricas obrigatórias, também é registrada a evolução da solução ao longo do trial.

A cada execução dos testes são coletados:

- número do ciclo;
- tempo decorrido;
- quantidade de testes passando;
- quantidade de testes falhando;
- taxa de sucesso.

Esses dados permitem analisar não apenas o resultado final, mas também como a solução evolui durante o experimento.

Com isso, será possível comparar se o uso de IA altera:

- a velocidade de progresso;
- a quantidade de ciclos de teste;
- o retrabalho necessário até atingir o estado `green`.

## Arquivos de saída

Os dados são armazenados em dois arquivos:

### `trials.csv`

Contém um registro consolidado por trial.

Exemplo de campos:

```text
participante,kata,tratamento,tempo_segundos,testes_passando,
testes_falhando,total_testes,taxa_sucesso,ciclos,status