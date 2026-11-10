# Lab04 — A taxa de falhas do CI ultrapassa 5%?

**Dashboard público** · [Abrir o Lab04 no Streamlit](https://lab04-medicao-pucminas.streamlit.app/)

Laboratório de Medição e Experimentação de Software da PUC Minas. No cenário
P4, comparamos o teste Z para uma proporção e o teste binomial exato sobre as
mesmas observações. A hipótese nula é **H₀: p ≤ 0,05** e a alternativa é
**H₁: p > 0,05**. Ambos são unilaterais à direita, com **α = 0,05** e
p-valores calculados na fronteira **p₀ = 0,05**. A regra adotada é rejeitar
H₀ quando o p-valor é estritamente menor que α.

## Integrantes

| Integrante | Contribuições |
|---|---|
| Islayder Jackson | Simulador, testes Z/binomial, Q1/Q2, auditoria estatística e testes |
| Fernanda Soares | Coleta e validação dos dados reais, Q3, resultados reais e interpretação |
| Vinicius Gomes | Dashboard Streamlit, gráficos Matplotlib G1–G4 e integração da interface |

## Dados reais

O snapshot [ci_runs.csv](data/ci_runs.csv) contém **169 execuções**, com
**162 sucessos e sete falhas**. A unidade é uma execução do workflow
**Test** (ID 1929523), na branch `master` do repositório `fastapi/fastapi`.
A coleta usou a API pública do GitHub Actions para execuções de `push`
concluídas de 1º de julho a 30 de setembro de 2026 (UTC). Incluímos
`success` (0) e `failure` (1) e excluímos oito execuções canceladas do
denominador. A regra de seleção, os links das execuções e a verificação do
snapshot estão descritos no [cenário da S01](docs/cenario_s01.md).

## Instalação e execução

Na raiz do repositório, crie um ambiente virtual com Python 3.13.

```bash
python -m venv .venv
```

Ative com `source .venv/bin/activate` em Linux/macOS ou com
`.\.venv\Scripts\Activate.ps1` no PowerShell. Depois execute:

```bash
python -m pip install -r lab04/requirements.txt
python -m streamlit run lab04/app.py
```

O dashboard abre em `http://localhost:8501` por padrão. A barra lateral
oferece navegação pelas sete seções. Os controles de tamanho, probabilidade
e semente alteram a amostra ilustrativa ajustável de G1/G2. O G1 também
mostra uma amostra simulada de referência com n = 200, gerada com a mesma
probabilidade e semente; apenas o tamanho desse terceiro painel é fixo.
A meta e o α ajustáveis valem para a exploração de G2. O cenário oficial, os resultados reais e
as simulações de G3/G4 usam p₀ e α de 5%.

G1 apresenta três painéis na mesma escala percentual: 169 execuções reais,
uma amostra simulada ajustável (n = 30 por padrão) e uma amostra simulada de
referência com n = 200. As duas amostras simuladas do G1 são exemplos individuais,
não as 10.000 repetições por cenário dos experimentos oficiais de G3/G4;
as contagens e proporções são calculadas a partir das amostras geradas.
G2 separa o p-valor observado da região crítica. G3 apresenta as
taxas de erro tipo I e a incerteza de Monte Carlo, e G4 compara o poder em
painéis com escalas compartilhadas.

O grupo precisa fornecer ou confirmar a URL do quadro GitHub Projects
associado ao Lab04. Depois de verificado, o endereço pode ser registrado
em `PROJECTS_URL` no arquivo `src/delivery_config.py`.

## Estrutura

| Caminho | Conteúdo |
|---|---|
| `app.py` | Cenário, dados (G1), testes (G2), erro tipo I (G3), poder (G4), resultados reais e conclusão |
| `src/simulation.py`, `src/stat_tests.py` | Gerador Bernoulli e testes aplicados à mesma amostra |
| `src/real_data.py`, `src/real_results.py`, `src/real_summary.py` | Validação dos dados, resultados, efeito e intervalo de confiança |
| `src/s02_experiments.py`, `src/robustness.py` | Simulações de Q1/Q2 e Q3 |
| `src/plots.py`, `src/captions.py`, `src/s02_results.py` | Gráficos, legendas e preparação das tabelas |
| `data/`, `results/` | Snapshot real e saídas simuladas, em diretórios separados |
| `tests/`, `docs/` | Testes automatizados, metodologia e [roteiro de apresentação e defesa](docs/apresentacao_final.md) |

## Reprodução e validação

```bash
python -m pytest -q lab04/tests
python -m lab04.src.final_audit --replay
python -m lab04.src.final_audit --replay --csv lab04/results/s02_q3.csv
```

O replay verifica e reproduz os valores armazenados, incluindo contagens,
taxas de rejeição e erros-padrão. Para gerar novamente as saídas versionadas:

| Etapa | Comando | Saída |
|---|---|---|
| Exemplo simulado S01 | `python -m lab04.src.example_s01` | JSON no terminal, versionado em `results/s01_example.json` |
| Q1/Q2, n = 200 | `python -m lab04.src.s02_experiments` | `results/s02_q1_q2.csv` |
| Q3, n = 30 | `python -m lab04.src.robustness` | `results/s02_q3.csv` |

Q1 usa p = p₀ para estimar o erro tipo I. Q2 usa seis efeitos de 0 a 15
pontos percentuais, com p = 5%, 7,5%, 10%, 12,5%, 15% e 20%. O ponto de
efeito zero corresponde a Q1. Q3 repete o desenho com n = 30. Em cada
condição, a semente é **42** e há **10.000 repetições por cenário**.
A mesma contagem de falhas em cada repetição alimenta os dois testes.
Para ler tabelas de outro diretório, defina `LAB04_RESULTS_DIR` antes de
executar o app. Para refazer a coleta real, execute
`python -m lab04.src.collect_ci_runs`. Esse comando grava o CSV novamente
com as conclusões disponíveis na API no momento da consulta.

## Interpretação

- **Amostra real.** A taxa observada foi 4,14%, efeito de −0,86 ponto
  percentual em relação à meta. O Z foi −0,512 (p = 0,6956) e o binomial
  exato observou K = 7 (p = 0,7452). A amostra fornece evidência
  insuficiente de que a taxa excede 5%. A seção 6 mostra também o h de Cohen
  e o intervalo bilateral exato de 95% para a proporção.
- **Q1 e Q2.** Em n = 200, ambos rejeitaram 4,48% sob H₀ e tiveram o mesmo
  poder em todos os cenários. As duas regras rejeitam a partir de 16
  falhas nesse desenho.
- **Q3.** Em n = 30, o Z foi liberal (6,05%) e o binomial exato,
  conservador (1,69%). As taxas teóricas sob p₀ são cerca de 6,08% e 1,56%.
  Com apenas 1,5 falha esperada, o Z rejeita a partir de quatro falhas e o
  exato a partir de cinco. A regra menos exigente do Z eleva o poder e
  também a frequência de falsos alarmes. Para falhas raras, prefira o
  binomial exato para respeitar o nível nominal sob o modelo.

A inferência supõe execuções independentes e probabilidade constante.
Execuções próximas podem compartilhar causas de falha e a taxa pode variar
no tempo. A amostra cobre um único workflow, branch e período. As taxas de
G3/G4 são estimativas de Monte Carlo para os cenários definidos.

## Publicação no Streamlit Community Cloud

A aplicação está publicada a partir da branch oficial `Laboratorio-4`.
Para reproduzir a publicação em um novo app, siga estes passos.

1. Entre no [Streamlit Community Cloud](https://share.streamlit.io/) com uma
   conta GitHub com acesso ao repositório.
2. Selecione **Create app** e **Yup, I have an app**.
3. Preencha **Repository** com `fesoaress/Laboratorio-Medicao-e-experimentacao`,
   **Branch** com `Laboratorio-4` e **Main file path** com `lab04/app.py`.
   Em **App URL**, escolha um subdomínio disponível para o novo app.
4. Em **Advanced settings**, selecione **Python 3.13** e clique em **Save**. O app lê arquivos
   versionados e dispensa segredos. O Cloud encontra `lab04/requirements.txt`
   no diretório do entry point. Confira a [organização de arquivos do Streamlit](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization).
5. Clique em **Deploy** e aguarde a instalação. Abra a URL gerada em
   uma janela sem sessão, confira as sete seções e os quatro gráficos
   em desktop e celular e compartilhe o endereço verificado com o grupo.

O deploy funciona com a configuração versionada. Se o endereço oficial mudar,
verifique o acesso público antes de atualizar os links no README e em
`src/delivery_config.py`.
