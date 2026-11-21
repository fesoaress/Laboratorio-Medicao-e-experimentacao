# Plano e evidências das sprints — Lab05

## S01 — Proposta e piloto (5 pontos)
**Problema:** em buscas pontuais SQLite, quanto a indexação reduz a latência? **Objeto:** SQLite real executado localmente. **Três critérios:** software existente, mantido e de alto impacto comprovado por páginas oficiais do projeto. **Método:** comparação pareada, duas tabelas com 60 mil registros sintéticos e 50 consultas por bloco. **Piloto:** 20 pares em 19/11/2026, tratado como estudo de viabilidade e excluído da inferência final. **Entregáveis:** GQM, RQs 1–3, sete categorias, hipóteses, métricas, plano de coleta/análise e piloto.

## S02 — Coleta, dados e inferência (5 pontos)
**Coleta principal:** 21/11/2026, Linux, Python 3.13.5 e SQLite 3.46.1, 10 sessões, 80 pares, 8.000 consultas SQL. **Rastreabilidade:** IDs de sessão/bloco/tratamento, ordem dos braços, tempos médios, metadados de versão, semente e SQL. **Validação:** pares completos, tempo positivo, dados idênticos, planos SQL coerentes. **Análise:** resumo por sessão, teste dos sinais unilateral e IC bootstrap reamostrando sessões. Resultado descritivo principal: 330,9×, p=0,00097656, IC 320,4×–355,4× para razão de medianas por sessão. Limitação: contexto exclusivamente local.

## S03 — Impacto e discussão (5 pontos)
**Impacto ilustrativo:** 10 mil buscas sequenciais similares: ~21,03 s sem e ~0,064 s com índice, diferença ~20,97 s. Não é economia real nem throughput. **Custo:** +644 KiB no arquivo. **7 categorias revisadas:** aplicada; explicativa; quantitativa; experimental; transversal com medidas repetidas; controlada pareada; evidência local de generalização restrita. **Ameaças:** conclusão, interna, construto e externa. **Saídas:** discussão por RQ, relatório, slides e roteiro.

## Entrega final — 10 minutos (5 pontos)
**Islayder, 3 min:** cenário, três critérios, pergunta, GQM, categorias. **Vinícius, 3min30s:** SQL, tratamentos, medição, confiabilidade. **Fernanda, 3min30s:** resultados, inferência, impacto e limites.

**Responsabilidades sugeridas**, não histórico confirmado de atividade individual.

**Pendências humanas:** validar reservas do software com o professor, criar/ligar GitHub Projects e issues reais, completar nomes, revisar o material e eventualmente refazer a medição no equipamento do grupo.
