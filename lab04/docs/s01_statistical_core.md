# Lab04 S01 — Núcleo estatístico (Issue #78)

## Pergunta e hipóteses

Para uma execução de um workflow de CI, definimos **1 = falha** e **0 = sucesso**. A pergunta é se a probabilidade real de falha ultrapassa 5%:

- **H₀:** p ≤ 0,05.
- **H₁:** p > 0,05 (teste unilateral à direita).
- **α = 0,05**; para a hipótese nula composta, ambos os testes calculam p-valores na fronteira p₀ = 0,05.

Assumimos execuções Bernoulli independentes com probabilidade de falha constante em cada cenário simulado. Essa suposição simplifica a realidade: falhas de CI podem ser correlacionadas e variar no tempo. A amostra real será coletada separadamente na Issue #77.

## Arquivos e interface para o dashboard

- `lab04/src/simulation.py`: `simulate_runs(n, p, seed=42) -> np.ndarray`, retornando um vetor unidimensional de 0 e 1.
- `lab04/src/stat_tests.py`: `evaluate_tests(data, p0=0.05, alpha=0.05) -> dict` com `n`, `k`, `p_hat`, `z_statistic`, `z_critical`, `z_p_value`, `binomial_p_value`, `reject_z`, `reject_binomial` e indicadores de validade da aproximação.
- `lab04/src/example_s01.py`: exemplo artificial com n=30, p real=0,10 e seed=42; pode ser executado com `python -m lab04.src.example_s01` na raiz do repositório.
- `lab04/tests/test_stat_tests.py`: `python -m pytest -q lab04/tests/test_stat_tests.py`.
- `lab04/results/s01_example.json`: saída do exemplo acima, exclusivamente **simulado**.

## Cálculos

O teste Z utiliza `Z = (p̂ − p₀) / sqrt(p₀(1 − p₀)/n)` e `P(Z_normal ≥ z_observado)` como p-valor; a região crítica é `z > norm.isf(α)`. Já o teste binomial exato utiliza `P(K ≥ k_observado | n, p₀)` sem aproximação normal.

Regra operacional: rejeitamos H₀ quando o p-valor for **estritamente menor que α**; caso contrário, **não rejeitamos** (o resultado não prova que H₀ seja verdadeira). A aproximação normal pode ser problemática quando `n*p₀ < 5` ou `n*(1-p₀) < 5` (sinalizador heurístico, não garantia de precisão quando acima do limite). Na S02 avaliaremos as taxas empíricas de erro tipo I e poder com 10.000 simulações por situação.

## Integração

O dashboard de Vinicius (#79) pode utilizar diretamente os dois métodos acima. No G2, mostrar a distribuição binomial discreta de K sob H₀ e a curva normal de Z como aproximação, marcando as regiões de rejeição e os respectivos p-valores do **mesmo exemplo simulado**. Os dados reais e parâmetros empíricos virão de Fernanda (#77).
