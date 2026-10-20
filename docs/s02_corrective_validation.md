# Validação empírica da heurística corretiva — #58

Em 20/10/2026, após três arquivos completos, o consenso foi finalizado usando
unanimidade/maioria e uma resolução humana de Islayder em `armbian/build`.
Os CSVs individuais foram preservados. A classe positiva é `yes`; os 300 itens
são alinhados por `item_id`, com predecessora no histórico completo.

| Versão | TP | FP | FN | TN | Precision | Recall | F1 | Resultado |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v1 | 96 | 156 | 14 | 34 | 0,380952 | 0,872727 | 0,530387 | Refinar |
| v2 | 106 | 115 | 4 | 75 | 0,479638 | 0,963636 | 0,640483 | Refinar |
| v3 | 48 | 5 | 62 | 185 | 0,905660 | 0,436364 | 0,588957 | Refinar |
| v4 | 57 | 9 | 53 | 181 | 0,863636 | 0,518182 | 0,647727 | Refinar |
| **v5** | **83** | **36** | **27** | **154** | **0,697479** | **0,754545** | **0,724891** | **Aceita** |

Precisão = TP/(TP+FP), recall = TP/(TP+FN), F1 = 2TP/(2TP+FP+FN).
Aceitação comparada sem arredondamento a 0,70. `selected_heuristic.json`
registra v5 como a primeira versão avaliada que atingiu o requisito.
Não houve refinamento após a aceitação. Os valores completos, flags de
denominadores, ambiente, hashes, fontes e código avaliado estão em cada pasta
`data/validation/corrective/vN/`; nenhuma execução foi sobrescrita.

## Alterações justificadas

- v1, baseline existente: patch SemVer ou sinal corretivo em qualquer commit.
  A regra muito abrangente produziu 156 falsos positivos.
- v2, alternativa existente: predominância de correções frente a features
  explícitas em notas/commits, fallback de patch, manutenção tipada ignorada.
  Falsos positivos persistiram: adições e outras mudanças ficavam sem sinal de
  feature e fora da comparação; patch isolado não demonstrava correção.
- v3: maioria estrita entre todas as entradas de mudança, notas com precedência,
  exclusão de rodapés/contribuidores/código, sem fallback de patch. Elevou a
  precisão, mas o denominador incluía muita manutenção e perdeu recall.
- v4: mesma maioria estrita entre mudanças funcionais, removendo manutenção,
  dependências, documentação, entradas administrativas e prefixos SHA. Recuperou
  parte do recall, mas o requisito não foi atingido.
- v5: refina o balanço lexical de v2, reconhecendo adições (`add`), introduções,
  suporte e melhorias como sinais funcionais concorrentes; manutenção e seções
  administrativas são ignoradas e patch isolado não decide. Empate é negativo.
  Corrigir uma funcionalidade que contém esses termos continua sendo correção.

As regras não recebem repositório, tag específica, `item_id` ou votos humanos
como condição. O diagnóstico usou contagens por regra e inspeção limitada de
erros, sem busca de limiar ou exceções por projeto. Todas as revisões foram
reavaliadas na mesma amostra: **validação interna com otimismo de seleção**,
sem teste externo independente. F1≥0,70 satisfaz o requisito operacional,
não demonstra causalidade, incidente real ou desempenho fora da amostra.

## Reprodução e aplicação à população

```powershell
python -m src.corrective_validation --version v5 --output-dir data/validation/corrective/nova_execucao_v5
python -m src.corrective_population --evaluation data/validation/corrective/v5/evaluation.json --output-dir data/processed/s02/nova_classificacao_v5
```

O classificador da população exige F1 aceito, fontes com os mesmos hashes e
implementação idêntica à avaliada (tolerando somente CRLF/LF na portabilidade
Windows/Linux, com hash bruto do snapshot preservado). Há 27.152 previsões em 311 repositórios,
com 26.972 classificações utilizáveis e 180 com contexto insuficiente
explicitamente marcadas. Notas com sinais funcionais permitem classificação;
na sua ausência, exige-se intervalo de commits completo. A previsão binária
bruta é preservada mesmo quando não utilizável, sem convertê-la em evidência
de ausência de correção.

Essas previsões **não são rótulos humanos**. A inspeção do código e das Issues
[#52](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/52)
e [#58](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/issues/58)
não encontrou detalhes suficientes para a agregação; por isso o grupo foi
consultado e confirmou a regra de qualquer corretiva posterior em até sete
dias e censura final incondicional. A implementação e os 311 valores de CFR(b)
seguem `docs/cfr_delivery_policy.md`, com fontes e avaliação v5 rastreáveis.
