# Roteiro da apresentação — Lab05 SQLite (10 min)

**Islayder — slides 1 a 3 (0:00–3:00):** apresentar o SQLite como software real, mantido e de alto impacto; explicar que o experimento é local e não mineração de repositório; pergunta central sobre impacto do índice; três RQs, GQM, hipóteses, sete categorias. Passar para o método de medição do Vinícius.

**Vinícius — slides 4 a 6 (3:00–6:30):** duas tabelas iguais com 60 mil registros; com e sem índice na coluna chave; consulta pontual idêntica; controle pareado. Dez sessões, oito pares de blocos por sessão, 50 consultas por braço e bloco, ordem alternada, 8.000 consultas. Medianas observadas 2,103 ms sem e 0,00635 ms com índice; aceleração descritiva cerca de 331 vezes. Ressaltar que a medida não é de produção.

**Fernanda — slides 7 a 10 (6:30–10:00):** resultado mais rápido com índice nas dez sessões; teste dos sinais unilateral p≈0,000977 (< 0,05); IC bootstrap da aceleração 320,4×–355,4× (limitado ao host). RQ2: SCAN versus SEARCH USING INDEX; RQ3: +644 KiB. Cenário ilustrativo de 10 mil buscas sequenciais: ~21,03 s versus ~0,064 s, não previsto em produção. Discutir ameaças à validade (conclusão, interna, construto, externa), concluir com recomendação de medir workloads reais.

**Perguntas possíveis:** Por que inferência por sessões e não por milhares de SQL? Para evitar pseudorreplicação. Por que experimentar localmente? Para não sobrecarregar serviço externo e controlar dados. O índice sempre melhora? Não; seletividade, escritas e carga mudam o resultado. Qual o motor de fato usado? SQLite 3.46.1.
