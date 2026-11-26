# Lab05 — Experimento em software real (SQLite)

**Pergunta:** quanto um índice secundário altera a latência de uma busca pontual no SQLite?

Projeto da disciplina **Laboratório de Experimentação de Software**, PUC Minas, prof. Danilo Maia. Grupo: Islayder, Vinícius e Fernanda.

**Software:** SQLite real em execução local, não mineração de repositório GitHub. **Dados:** sintéticos. **Snapshot medido:** SQLite 3.46.1, Python 3.13.5, Linux, 21/11/2026.

| Resultado deste ambiente | Valor |
|---|---:|
| Registros por tabela | 60.000 |
| Consultas por tratamento | 4.000 |
| Mediana sem índice | 2,10297 ms |
| Mediana com índice | 0,006355 ms |
| Redução descritiva | 99,70% |
| Teste unilateral dos sinais, 10 sessões | p = 0,000977 |
| Armazenamento extra do índice | 644 KiB |

Esses resultados são de um benchmark local específico e **não representam desempenho garantido em produção**.

## Divisão do trio no GitHub

[Ver plano de 12 issues por sprint e integrante](documentos/Plano_Issues_Sprints.md). A divisão representa responsabilidades propostas; não presume a execução histórica por cada integrante.

## Entregas

- **S01 (5 pontos):** proposta, critérios do software, hipóteses, GQM, sete categorias e piloto.
- **S02 (5 pontos):** execução, validação, dados e análise inferencial.
- **S03 (5 pontos):** interpretação, impacto hipotético e ameaças à validade.
- **Final (5 pontos):** documento no [modelo do professor](documentos/Relatorio_Modelo_Professor.md) e apresentação de 10 minutos.

## Documentação

O relatório do repositório usa as seções exigidas pelo arquivo `Template_Relatorio_Laboratorio.docx`: Introdução, Contexto, Metodologia (3.1–3.6), Resultados (4.1–4.3), Conclusão e Referências.

O pacote local inclui também uma versão DOCX/PDF do mesmo relatório, os gráficos, os slides e os scripts completos. Estes arquivos binários **ainda não estão nesta branch do GitHub**; não são substituídos por links de sandbox. Os scripts e resultados versionados identificam a medição; verificar contra o pacote original antes da entrega.

## Reprodutibilidade

- Coleta local: Python, SQLite, tabela sintética e 10 sessões.
- Arquivos de dados desta branch: `dados/resumo_sessoes.csv`, `dados/analise.json`, `dados/metadados.json`.
- Atenção: a leitura de benchmarks precisa separar o piloto da coleta principal e não tratar as 8.000 consultas como observações independentes.

**Pendências:** registrar as issues/Projects, confirmar que outro grupo não escolheu SQLite, preencher nomes completos e realizar a revisão do trio. Os dados foram gerados em ambiente computacional de apoio, não declarados como coleta pessoal dos integrantes.
