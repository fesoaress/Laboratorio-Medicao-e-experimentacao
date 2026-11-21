# Relatório de Laboratório — LAB05

**Disciplina:** Laboratório de Experimentação de Software | **Professor:** Danilo Maia | **Grupo:** Islayder, Vinícius e Fernanda (nomes completos a conferir) | **Data:** 21/11/2026

**Experimento:** impacto de índices secundários na latência de consultas pontuais no SQLite.

**Repositório:** [Laboratorio-5/lab05](https://github.com/fesoaress/Laboratorio-Medicao-e-experimentacao/tree/Laboratorio-5/lab05). **GitHub Projects:** link a preencher pelo grupo.

> **Origem dos dados:** experimento real executado em um ambiente Linux disponibilizado nesta conversa, com registros sintéticos. Não foi executado em produção nem no computador dos integrantes. Os valores precisam ser assumidos e revisados pelo grupo antes da entrega.

## 1. Introdução

Este estudo avalia um problema de otimização de software real: índices secundários podem acelerar buscas SQL, mas ocupam armazenamento e precisam ser mantidos nas gravações. A comparação não deve partir de uma suposição de que índices sempre são melhores.

**RQ1:** Quanto o índice reduz a latência de uma busca pontual em uma tabela de 60.000 linhas?

**RQ2:** O plano de execução muda de \`SCAN\` para \`SEARCH ... USING INDEX\`?

**RQ3:** Quanto espaço adicional o índice exige?

**Hipóteses informais anteriores à coleta:** esperávamos ganho de latência em RQ1, mudança de plano em RQ2 e aumento de espaço em RQ3. As RQs são propostas pelo grupo; o Lab05 é de formato livre.

**Contribuição adicional:** relacionar latência, mecanismo SQL, custo de armazenamento e reprodutibilidade por sessões (detalhada na seção 3.6).

## 2. Contexto

O SQLite é um motor SQL embarcado real, mantido e amplamente distribuído em aparelhos e aplicações. Evidências: [About SQLite](https://www.sqlite.org/about.html), [Release History](https://www.sqlite.org/changes.html) e [Most Widely Deployed](https://www.sqlite.org/mostdeployed.html). A estimativa de alcance divulgada na página oficial é do mantenedor, não contagem auditada de usuários.

Este laboratório avalia **o SQLite em execução**, não um repositório do GitHub. A coleta mediu a biblioteca SQLite **3.46.1**, disponível no Python **3.13.5** do ambiente Linux, e não uma versão mais nova em produção. Reaproveita dos Labs anteriores a instrumentação automatizada (Lab01), comparação de tratamentos (Lab02), leitura de métricas operacionais (Lab03) e inferência estatística (Lab04).

## 3. Metodologia

### 3.1 Principais Desafios

A medição de consultas com poucos microssegundos é sensível a aquecimento de cache, escalonamento de CPU e overhead do Python. Foram cronometrados blocos de consultas em vez de tratar cada duração como replicação independente. O estudo tem 10 sessões, com conexões separadas; sessões sequenciais no mesmo host ainda podem ser correlacionadas.

### 3.2 Tomadas de Decisão

**GQM, objetivo (Basili):** analisar a presença de um índice secundário no SQLite para avaliar o efeito da indexação sobre a latência de buscas pontuais e o armazenamento, do ponto de vista do desenvolvedor, em um experimento local com dados sintéticos.

- **Q1:** o índice reduz a latência? Métricas: mediana em ms/consulta, diferença e razão entre cenários.
- **Q2:** o plano SQL muda? Métrica: categoria nominal retornada pelo EXPLAIN QUERY PLAN.
- **Q3:** quanto custa em espaço? Métrica: variação de páginas do banco, convertida em bytes/KiB.

**Entidade:** motor SQLite executando uma base. **Atributos:** latência observável (externo), presença do índice e plano (internos), arquivo em bytes (recurso). **Medida direta:** tempo total de bloco e número/tamanho de páginas. **Derivadas:** ms por consulta, diferenças, redução percentual e razão de aceleração. Tempos, bytes e contagens estão em escala de razão; nomes dos tratamentos e tipos de plano são nominais.

**Hipótese estatística de RQ1:** para cada sessão, D = mediana(sem índice) - mediana(com índice). H₀: mediana de D ≤ 0; H₁: mediana de D > 0. Alfa = 0,05. Teste exato unilateral dos sinais sobre as 10 sessões; bootstrap percentil com 20.000 reamostragens de sessões, não das consultas individuais. A razão entre medianas de blocos é uma medida descritiva, diferente do estimando testado.

**Tratamentos:** A = tabela \`pedidos_sem\` sem índice secundário sobre \`chave\`; B = tabela \`pedidos_com\` com índice \`idx_chave_pedidos_com\` sobre \`chave\`. Ambas armazenam as mesmas 60.000 linhas e valores. Consulta: \`SELECT valor FROM pedidos_* WHERE chave = ?\` com chave única por linha. Variável independente: presença do índice. Variável dependente: tempo por consulta. Controles: dados, consulta, chaves, motor, máquina, condições de cache, quantidade de buscas e ordem intercalada.

**Sete categorias de pesquisa:**

| Categoria | Classificação e justificativa |
|---|---|
| Natureza | Aplicada: decisão técnica de otimização |
| Objetivos | Explicativa: manipula a indexação e examina o mecanismo |
| Abordagem | Quantitativa: latência e espaço numericamente mensuráveis |
| Procedimentos | Experimental em laboratório: dois tratamentos |
| Tempo | Transversal com medidas repetidas: uma campanha, múltiplas sessões |
| Controle | Controlado e pareado: mesmas chaves e dados, ordem alternada |
| Nível de evidência | Experimento local com generalização restrita |

### 3.3 Etapas

| Entrega | Evidência | Papel sugerido |
|---|---|---|
| Lab05S01 (5 pt) | Proposta, critérios do software, GQM, categorias, piloto com 20 pares | Islayder: método; Vinícius: coleta; Fernanda: análise |
| Lab05S02 (5 pt) | Coleta com 80 pares, métricas, validação, análise e ameaças à validade | Vinícius: execução; Fernanda: estatística; Islayder: validade |
| Lab05S03 (5 pt) | Interpretação, impacto, conclusões, limitações | Fernanda: impacto; Islayder: documento; Vinícius: SQL |
| Final (5 pt) | Relatório do modelo do professor e apresentação de 10 minutos | Trio |

Os papéis acima são **proposta de divisão**, não atribuição de execução histórica pelos estudantes. A captura do Kanban e os números reais das issues serão preenchidos após o GitHub Projects ser organizado.

### 3.4 Ferramentas

Python 3.13.5, biblioteca sqlite3 (SQLite 3.46.1), Linux x86_64, \`time.perf_counter_ns()\`, seed 20261121, SQLite com \`PRAGMA automatic_index=OFF\`, cache ~2 MiB e \`temp_store=MEMORY\`. Análise com pandas, NumPy, SciPy (\`binomtest\`), Matplotlib; artefatos: CSV por blocos, CSV por sessão e JSON de metadados/resultados. A reexecução deve conservar o snapshot original em outra pasta.

### 3.5 Tabela de Métricas

| RQ | Métrica | Definição operacional | Unidade | Fonte |
|---|---|---|---|---|
| RQ1 | Tempo por consulta | Tempo de execução do bloco / 50 buscas | ms/consulta | medicoes_blocos.csv |
| RQ1 | Mediana | Mediana de 80 médias por bloco, por cenário | ms/consulta | medicoes_blocos.csv |
| RQ1 | Diferença e aceleração | Mediana(A)-Mediana(B); Mediana(A)/Mediana(B) | ms; vezes | analise.json |
| RQ1 | p-valor | Teste exato unilateral dos sinais em 10 sessões | probabilidade | resumo_sessoes.csv |
| RQ2 | Plano | Resultado do EXPLAIN QUERY PLAN | nominal | metadados.json |
| RQ3 | Espaço | (pages_after-pages_before) x page_size | bytes/KiB | metadados.json |

### 3.6 Inovações Propostas pelo Grupo (30% da nota)

Acrescentamos à comparação de tempos a **triangulação entre plano real do otimizador SQL, espaço ocupado pelo índice e robustez da medição por sessões**. Parear consultas pelas mesmas 50 chaves, alternar a ordem, evitar pseudorreplicação das 8.000 chamadas SQL e entregar scripts reproduzíveis fortalece a transparência. O título desta seção vem do modelo geral do professor; o enunciado específico do Lab05 mantém avaliação de formato livre.

## 4. Resultados

### 4.1 Coleta de Dados

Duas tabelas sintéticas de 60.000 registros; 10 sessões × 8 pares de blocos × 50 consultas por tratamento = **8.000 buscas SQL**, sendo 4.000 com e 4.000 sem índice. O CSV contém 160 linhas de medição e 80 pares completos, sem tempos nulos, tratamentos ausentes ou duplicados. Piloto de 20 pares realizado separadamente em 19/11/2026; coleta completa em 21/11/2026, ~14h45 UTC. A análise final não mistura piloto e coleta principal.

### 4.2 Visualização Gráfica

**RQ1 — Latência:** 2,10297 ms sem índice versus 0,006355 ms com índice. A pasta de gráficos do pacote local contém a comparação, a aceleração das sessões e os boxplots logarítmicos.

**RQ2 — Planos SQL:** \`SCAN pedidos_sem\` sem índice; \`SEARCH pedidos_com USING INDEX idx_chave_pedidos_com (chave=?)\` com índice. Trata-se de categorias nominais; a diferença é visualizada em um diagrama comparativo.

**RQ3 — Espaço:** 1.101 páginas antes do índice e 1.262 depois, com páginas de 4.096 bytes, ou 644 KiB adicionais.

### 4.3 Discussão

**RQ1, expectativa confirmada no ambiente testado:** mediana por bloco sem índice **2,10297321 ms**, com índice **0,00635496 ms**. A diferença foi **2,09661825 ms**, aceleração de **330,9×**, redução de latência de **99,70%**. Dez de dez sessões favoreceram o índice, teste unilateral dos sinais **p = 0,0009765625** (α = 0,05), rejeitando H₀ para este experimento. Bootstrap percentil (95%) para razão de medianas por sessão: **320,4× a 355,4×**, refletindo apenas a variabilidade neste host.

**RQ2, expectativa confirmada:** o plano mudou de varredura para pesquisa apoiada pelo índice, conforme EXPLAIN QUERY PLAN.

**RQ3, expectativa confirmada:** o índice acrescentou **161 páginas = 659.456 bytes = 644 KiB**. Não foi medido o impacto de inserções, atualizações ou concorrência.

**Impacto ilustrativo:** extrapolando linearmente as medianas locais, 10.000 buscas sequenciais idênticas seriam ~21,03 s sem índice e ~0,064 s com índice (diferença ~20,97 s). Isso **não é medição de throughput**, SLA, economia corporativa nem previsão para 10.000 usuários simultâneos.

**Validade de conclusão:** 10 sessões sequenciais podem ser autocorrelacionadas e o temporizador é ruidoso; agregamos por sessão. **Validade interna:** cache, CPU e ordem parcialmente controlados; não há isolamento completo do sistema operacional. **Validade de construto:** uma consulta pontual por chave única não representa todas as consultas e inclui overhead de Python. **Validade externa:** um host Linux, SQLite 3.46.1 e dados sintéticos limitam generalização.

## 5. Conclusão

Neste benchmark local, o índice foi associado à redução descritiva de **99,70%** da latência mediana, com evidência estatística favorável (p unilateral 0,000977); o plano mudou de SCAN para SEARCH USING INDEX; o custo adicional foi de 644 KiB. A recomendação para aplicações reais é **medir consultas representativas, examinar planos e custos antes de decidir indexar**. O estudo não permite garantir o mesmo ganho em produção.

**Antes de entregar:** confirmar se o SQLite está disponível ao grupo; completar nomes, GitHub Projects e issues; revisar e eventualmente reexecutar no computador do grupo; confirmar cronograma.

## 6. Referências

1. SQLite, [About SQLite](https://www.sqlite.org/about.html), acesso em 21 nov. 2026.
2. SQLite, [Release History](https://www.sqlite.org/changes.html), acesso em 21 nov. 2026.
3. SQLite, [Most Widely Deployed](https://www.sqlite.org/mostdeployed.html), acesso em 21 nov. 2026.
4. SQLite, [EXPLAIN QUERY PLAN](https://www.sqlite.org/eqp.html), acesso em 21 nov. 2026.
5. PUC Minas, Prof. Danilo Maia. Enunciado Lab05, 2026.
6. Arquivos auditáveis deste estudo: medicoes_blocos.csv, resumo_sessoes.csv, analise.json e metadados.json; dados sintéticos locais.
7. Vídeo indicado no template do professor: https://www.youtube.com/shorts/YwnaeO95AN8 (não utilizado como fonte dos resultados).
