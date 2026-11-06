# Lab04 Final — Auditoria estatística e apresentação (Issue #84)

## O que conseguimos fazer sem esperar o dashboard

O código em \`lab04/src/final_audit.py\` verifica que os resultados de Q1/Q2 incluem:
- pelo menos cinco tamanhos de efeito e um cenário de **efeito zero**;
- as mesmas condições experimentais (n, p₀, α, seed e 10.000 repetições por cenário);
- proporções de rejeição compatíveis com as contagens;
- efeitos em pontos percentuais corretamente calculados;
- erros padrão de Monte Carlo coerentes;
- ausência de duplicação de efeitos;
- reprodução opcional exata do CSV pela seed e pelos parâmetros.

Executar na raiz, após instalar as dependências de NumPy, SciPy e pytest:

\`\`\`bash
python -m pytest -q lab04/tests/test_dashboard_integration.py
python -m lab04.src.final_audit --replay
\`\`\`

Esta auditoria cobre **a camada estatística, não a renderização final**. O teste não pode garantir que os gráficos G2/G3/G4 estejam corretos antes de os módulos de visualização estarem presentes.

## Checagem de integração quando o dashboard estiver disponível

- [ ] S01 (#77): dados reais novos, URL de origem, período, n, k, p̂ e exclusões documentadas.
- [ ] S01 (#79): G1 e G2 exibem legendas, unidades, cores consistentes e interpretações.
- [ ] S02 (#82): Q3 executado com n pequeno e 10.000 amostras por efeito, incluindo p_real=p₀.
- [ ] S02 (#83): G3 mostra erro tipo I e referência 5%; G4 mostra pelo menos cinco efeitos começando em zero; as curvas refletem as contagens.
- [ ] Tabela final: estatística, p-valor, tamanho do efeito e conclusão **para cada teste em dados reais**.
- [ ] Seções do dashboard na ordem: cenário; dados/G1; testes/G2; erro tipo I/G3; poder/G4; dados reais; conclusão.
- [ ] Quatro gráficos com 2–4 frases explicativas, links do dashboard e repo/Projects no topo; dashboard executa com comando único ou URL publicada.
- [ ] Nenhum resultado simulado é apresentado como observado; não afirmar que p-valor é probabilidade de H₀ ser verdadeira.
- [ ] Revisar README, CI, Issues/Projects, PRs e duração da apresentação (máximo 7 min).

## Respostas de Islayder — perguntas 2, 5, 7, 8 e 12

**2. Unicaudal ou bicaudal?** Unicaudal à direita: investigamos se p > 0,05, não qualquer diferença em relação a 5%.

**5. O que os testes comparam?** Os dois avaliam a quantidade/proporção de falhas frente a uma taxa de referência de 5%. O Z aproxima sua estatística pela normal; o binomial exato usa a probabilidade discreta exata sob H₀. Ambos trabalham na fronteira p₀ = 0,05.

**7. O que significa p-valor?** É a probabilidade, **sob a hipótese nula na fronteira p=5%**, de observar resultado tão extremo ou mais extremo na direção de H₁. Não é a probabilidade de H₀ estar certa ou errada e não mede o tamanho do efeito.

**8. Erros tipo I e II?** Tipo I: indicar uma taxa acima de 5% quando ela na verdade não excede esse valor (falso alarme). Tipo II: deixar de detectar que a taxa real excede 5% (falha que passa despercebida). Num CI, consideramos o tipo II potencialmente mais grave por deixar um problema real sem investigação; a prioridade pode mudar conforme o custo de cada erro.

**12. Se α baixar de 0,05 para 0,01?** A região de rejeição fica mais exigente. Em geral, **erro tipo I cai e poder também cai**, se tamanho amostral e efeito permanecerem iguais; o risco de tipo II cresce. É preciso reexecutar/avaliar os dois testes com α=0,01, não reaproveitar as mesmas taxas de rejeição.

Todos devem conhecer as 15 perguntas: a divisão é para organização, não limita a arguição do professor.

## Dependências e status

A S01 foi recuperada no PR #87; Q1/Q2 estão no PR #88. Esta Issue (#84) fica **parcialmente implementada** até existirem o dashboard e a análise Q3, com integração e validação finais. Nenhuma conclusão sobre os testes em dados reais deve ser inventada.
